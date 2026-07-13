import json
import logging
import os
from typing import Any, Callable, TypeVar

import httpx
from fastapi import FastAPI, HTTPException, Request
from langfuse import get_client, propagate_attributes
from langfuse.openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

from models import (
    EnrichmentRequest,
    EnrichmentResult,
    ManualReviewRequest,
    ManualReviewResult,
    OutboundEmailRequest,
    OutboundEmailResult,
    SalesMemoRequest,
    SalesMemoResult,
    ScoringRequest,
    ScoringResult,
    WeeklyInsightsRequest,
    WeeklyInsightsResult,
)
from observability import (
    LatencyTracker,
    attach_incoming_trace_context,
    build_crm_propagate_metadata,
    build_crm_trace_input,
    build_enrichment_trace_output,
    build_failed_trace_output,
    build_outbound_email_trace_output,
    build_sales_memo_trace_output,
    build_scoring_trace_output,
    build_weekly_insights_trace_output,
    build_trace_context_from_headers,
    classify_exception,
    content_hash,
    detach_trace_context,
    get_correlation_id_from_headers,
    preview,
    truncate_for_llm,
)
from prompt_loader import PromptTemplate, load_prompt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
SERVICE_VERSION = os.getenv("OTEL_SERVICE_VERSION", "v1.0")
ENVIRONMENT = (
    os.getenv("ENVIRONMENT")
    or os.getenv("LANGFUSE_TRACING_ENVIRONMENT")
    or "development"
)
os.environ.setdefault("LANGFUSE_TRACING_ENVIRONMENT", ENVIRONMENT)

if not DEEPSEEK_API_KEY:
    raise ValueError("DEEPSEEK_API_KEY environment variable is not set")

langfuse = get_client()
logger.info("Langfuse host: %s, environment: %s", os.getenv("LANGFUSE_HOST", "not-set"), ENVIRONMENT)
try:
    langfuse.auth_check()
    logger.info("Langfuse auth_check passed")
except Exception as exc:
    logger.warning("Langfuse auth_check failed: %s", exc)

proxy_url = os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
http_client = None
if proxy_url:
    transport = httpx.AsyncHTTPTransport(proxy=proxy_url)
    http_client = httpx.AsyncClient(mounts={"all://": transport})

client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL,
    http_client=http_client,
)

app = FastAPI(title="CRM Lead AI Service", version=SERVICE_VERSION)

T = TypeVar("T", bound=BaseModel)


@app.middleware("http")
async def propagate_w3c_trace_context(request: Request, call_next):
    token = attach_incoming_trace_context(request.headers)
    try:
        return await call_next(request)
    finally:
        detach_trace_context(token)


def _mark_generation_error(message: str) -> None:
    try:
        langfuse.update_current_generation(level="ERROR", status_message=message[:500])
    except Exception:
        logger.debug("No active Langfuse generation to mark as error", exc_info=True)


def _fallback_scoring(reason: str) -> ScoringResult:
    return ScoringResult(
        score=0,
        score_reasoning=reason,
        confidence="low",
        recommended_action="manual_review",
        intent_signals=[],
        routing_decision="fallback_scoring",
        fallback_used=True,
    )


def _fallback_sales_memo(content_summary: str) -> SalesMemoResult:
    opener = preview(content_summary, 300) or "Review lead summary before outreach."
    return SalesMemoResult(
        company_background=[],
        talking_points=[],
        pain_hypotheses=[],
        recommended_opener=opener,
        fallback_used=True,
    )


def _fallback_weekly_insights(metrics: dict[str, Any]) -> WeeklyInsightsResult:
    new_leads = metrics.get("new_leads", 0)
    high_score = metrics.get("high_score_leads", 0)
    booked = metrics.get("meetings_booked", 0)
    week_start = metrics.get("week_start", "")
    week_end = metrics.get("week_end", "")
    summary = (
        f"Week {week_start}–{week_end}: {new_leads} new leads, "
        f"{high_score} high-score, {booked} meetings booked. "
        "Metrics-only summary (AI unavailable)."
    )
    recommendations: list[str] = []
    if high_score > booked:
        recommendations.append("Follow up on high-score leads without bookings")
    if metrics.get("review_pending", 0) > 0:
        recommendations.append("Clear pending manual reviews")
    return WeeklyInsightsResult(
        executive_summary=summary,
        key_trends=[],
        recommendations=recommendations,
        anomalies=[],
        fallback_used=True,
    )


def _fallback_outbound_email(
    *,
    contact_name: str,
    company_name: str,
    content_summary: str,
    sales_memo_raw: str,
    calendly_url: str,
) -> OutboundEmailResult:
    opener = preview(content_summary, 300) or "I noticed your recent inquiry and wanted to reach out."
    try:
        memo = json.loads(sales_memo_raw) if sales_memo_raw else {}
        if memo.get("recommended_opener"):
            opener = memo["recommended_opener"]
    except json.JSONDecodeError:
        pass

    company = company_name or "your team"
    first_name = (contact_name or "").split()[0] or "there"
    cta = f"\n\nWould you be open to a quick chat? {calendly_url}" if calendly_url else "\n\nWould you be open to a quick reply?"
    body = f"Hi {first_name},\n\n{opener}\n\nI'd love to learn more about what {company} is working on and share how we might help.{cta}\n\nBest regards"

    return OutboundEmailResult(
        subject=f"Quick note for {company}"[:60],
        body=body,
        personalization_notes="Fallback draft from content summary / sales memo opener",
        fallback_used=True,
    )


async def _call_llm_json(
    *,
    prompt: PromptTemplate,
    prompt_vars: dict[str, str],
    span_name: str,
    generation_name: str,
    request: Request,
    lead_id: str,
    correlation_id: str,
    source_type: str,
    company_name: str,
    company_domain: str,
    contact_role: str,
    trace_input: dict[str, Any],
    result_model: type[T],
    fallback_factory: Callable[[], T] | None = None,
) -> T:
    header_correlation = get_correlation_id_from_headers(request.headers)
    effective_correlation = correlation_id or header_correlation or lead_id
    upstream_trace_context = build_trace_context_from_headers(request.headers)
    if upstream_trace_context:
        logger.info(
            "Continuing upstream trace_id=%s correlation_id=%s",
            upstream_trace_context["trace_id"],
            effective_correlation,
        )
    else:
        logger.warning(
            "No traceparent header; Langfuse trace may not link to Jaeger (correlation_id=%s)",
            effective_correlation,
        )

    rendered = prompt.render(**prompt_vars)
    tracker = LatencyTracker()

    with langfuse.start_as_current_observation(
        as_type="span",
        name=span_name,
        trace_context=upstream_trace_context,
        input=trace_input,
    ) as root_span:
        with propagate_attributes(
            tags=["crm-workflow"],
            version=SERVICE_VERSION,
            session_id=content_hash(effective_correlation),
            metadata=build_crm_propagate_metadata(
                lead_id=lead_id,
                correlation_id=effective_correlation,
                source_type=source_type,
                company_name=company_name,
                company_domain=company_domain,
                contact_role=contact_role,
                model_name=DEEPSEEK_MODEL,
                prompt_version=prompt.version,
                prompt_hash_value=prompt.prompt_hash,
            ),
        ):
            try:
                completion = await client.chat.completions.create(
                    model=DEEPSEEK_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that outputs only valid JSON."},
                        {"role": "user", "content": rendered},
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"},
                    timeout=45,
                    name=generation_name,
                    metadata={
                        "prompt_version": prompt.version,
                        "prompt_hash": prompt.prompt_hash,
                        "correlation_id": effective_correlation,
                        "lead_id": lead_id,
                    },
                )

                if not completion.choices:
                    raise ValueError("Empty response from LLM")

                raw = completion.choices[0].message.content
                usage = completion.usage
                input_tokens = usage.prompt_tokens if usage else None
                output_tokens = usage.completion_tokens if usage else None
                latency_ms = tracker.latency_ms

                with langfuse.start_as_current_observation(
                    as_type="span",
                    name="parse-and-validate",
                    input={"raw_json_preview": preview(raw, 500)},
                ) as parse_span:
                    result_json = json.loads(raw)
                    validated = result_model(**result_json)
                    trace_output = (
                        build_scoring_trace_output(result_json)
                        if result_model is ScoringResult
                        else build_enrichment_trace_output(result_json)
                        if result_model is EnrichmentResult
                        else build_sales_memo_trace_output(result_json)
                        if result_model is SalesMemoResult
                        else build_outbound_email_trace_output(result_json)
                        if result_model is OutboundEmailResult
                        else build_weekly_insights_trace_output(result_json)
                        if result_model is WeeklyInsightsResult
                        else result_json
                    )
                    parse_span.update(output=trace_output, metadata={"validation_status": "success"})

                root_span.set_trace_io(output=trace_output)
                root_span.update(
                    metadata=build_crm_propagate_metadata(
                        lead_id=lead_id,
                        correlation_id=effective_correlation,
                        source_type=source_type,
                        company_name=company_name,
                        company_domain=company_domain,
                        contact_role=contact_role,
                        score=result_json.get("score") if isinstance(result_json, dict) else None,
                        score_reasoning=result_json.get("score_reasoning") if isinstance(result_json, dict) else None,
                        recommended_action=result_json.get("recommended_action") if isinstance(result_json, dict) else None,
                        model_name=DEEPSEEK_MODEL,
                        prompt_version=prompt.version,
                        prompt_hash_value=prompt.prompt_hash,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        latency_ms=latency_ms,
                        confidence=result_json.get("confidence") if isinstance(result_json, dict) else None,
                        enrichment_summary=result_json.get("enrichment_summary") if isinstance(result_json, dict) else None,
                        routing_decision=result_json.get("routing_decision") if isinstance(result_json, dict) else None,
                    )
                )
                return validated

            except json.JSONDecodeError as exc:
                root_span.set_trace_io(output=build_failed_trace_output("json_parse_error", "parse"))
                _mark_generation_error(str(exc))
                if fallback_factory:
                    return fallback_factory()
                raise HTTPException(status_code=502, detail="Invalid JSON format from AI")

            except ValidationError as exc:
                root_span.set_trace_io(output=build_failed_trace_output("schema_validation_error", "parse"))
                _mark_generation_error(str(exc))
                if fallback_factory:
                    return fallback_factory()
                raise HTTPException(status_code=502, detail="Invalid JSON format from AI")

            except HTTPException:
                raise

            except Exception as exc:
                error_type, error_stage, status_code = classify_exception(exc)
                root_span.set_trace_io(output=build_failed_trace_output(error_type, error_stage))
                _mark_generation_error(str(exc))
                if fallback_factory:
                    return fallback_factory()
                if status_code == 502:
                    raise HTTPException(status_code=502, detail=f"AI Provider Error: {exc}")
                raise HTTPException(status_code=500, detail=f"Internal Server Error: {exc}")


@app.post("/enrich", response_model=EnrichmentResult)
async def enrich_lead(item: EnrichmentRequest, request: Request):
    raw_content, _ = truncate_for_llm(item.raw_content)
    prompt = load_prompt("lead_summary")
    return await _call_llm_json(
        prompt=prompt,
        prompt_vars={
            "contact_name": item.contact_name,
            "contact_email": item.contact_email,
            "contact_role": item.contact_role,
            "company_name": item.company_name,
            "company_domain": item.company_domain,
            "domain_type": item.domain_type,
            "source_type": item.source_type,
            "source_name": item.source_name,
            "raw_content": raw_content,
            "external_enrichment": item.external_enrichment,
        },
        span_name="crm-lead-enrichment",
        generation_name="deepseek-lead-enrichment",
        request=request,
        lead_id=item.lead_id,
        correlation_id=item.correlation_id,
        source_type=item.source_type,
        company_name=item.company_name,
        company_domain=item.company_domain,
        contact_role=item.contact_role,
        trace_input=build_crm_trace_input(
            lead_id=item.lead_id,
            correlation_id=item.correlation_id,
            source_type=item.source_type,
            contact_email=item.contact_email,
            company_name=item.company_name,
            raw_content=item.raw_content,
        ),
        result_model=EnrichmentResult,
        fallback_factory=lambda: EnrichmentResult(
            content_summary=preview(item.raw_content, 300),
            industry="unknown",
            company_size="unknown",
            intent_signals=[],
            enrichment_summary="LLM enrichment failed; using fallback partial data",
        ),
    )


@app.post("/score", response_model=ScoringResult)
async def score_lead(item: ScoringRequest, request: Request):
    prompt = load_prompt("lead_scoring")
    return await _call_llm_json(
        prompt=prompt,
        prompt_vars={
            "contact_name": item.contact_name,
            "contact_email": item.contact_email,
            "contact_role": item.contact_role,
            "company_name": item.company_name,
            "company_domain": item.company_domain,
            "industry": item.industry,
            "company_size": item.company_size,
            "source_type": item.source_type,
            "source_name": item.source_name,
            "source_trust_level": str(item.source_trust_level),
            "content_summary": item.content_summary,
            "intent_signals": ", ".join(item.intent_signals),
            "enrichment_status": item.enrichment_status,
            "enrichment_summary": item.enrichment_summary,
        },
        span_name="crm-lead-scoring",
        generation_name="deepseek-lead-scoring",
        request=request,
        lead_id=item.lead_id,
        correlation_id=item.correlation_id,
        source_type=item.source_type,
        company_name=item.company_name,
        company_domain=item.company_domain,
        contact_role=item.contact_role,
        trace_input=build_crm_trace_input(
            lead_id=item.lead_id,
            correlation_id=item.correlation_id,
            source_type=item.source_type,
            contact_email=item.contact_email,
            company_name=item.company_name,
            raw_content=item.content_summary,
        ),
        result_model=ScoringResult,
        fallback_factory=lambda: _fallback_scoring("LLM scoring failed; routed to manual review"),
    )


@app.post("/sales-memo", response_model=SalesMemoResult)
async def sales_memo(item: SalesMemoRequest, request: Request):
    prompt = load_prompt("sales_memo")
    return await _call_llm_json(
        prompt=prompt,
        prompt_vars={
            "contact_name": item.contact_name,
            "contact_email": item.contact_email,
            "contact_role": item.contact_role,
            "company_name": item.company_name,
            "company_domain": item.company_domain,
            "industry": item.industry,
            "company_size": item.company_size,
            "source_type": item.source_type,
            "source_name": item.source_name,
            "content_summary": item.content_summary,
            "intent_signals": ", ".join(item.intent_signals),
            "enrichment_summary": item.enrichment_summary,
            "score": str(item.score),
            "score_reasoning": item.score_reasoning,
            "recommended_action": item.recommended_action,
        },
        span_name="crm-sales-memo",
        generation_name="deepseek-sales-memo",
        request=request,
        lead_id=item.lead_id,
        correlation_id=item.correlation_id,
        source_type=item.source_type,
        company_name=item.company_name,
        company_domain=item.company_domain,
        contact_role=item.contact_role,
        trace_input=build_crm_trace_input(
            lead_id=item.lead_id,
            correlation_id=item.correlation_id,
            source_type=item.source_type,
            contact_email=item.contact_email,
            company_name=item.company_name,
            raw_content=item.content_summary,
        ),
        result_model=SalesMemoResult,
        fallback_factory=lambda: _fallback_sales_memo(item.content_summary),
    )


@app.post("/outbound-email", response_model=OutboundEmailResult)
async def outbound_email(item: OutboundEmailRequest, request: Request):
    prompt = load_prompt("outbound_email")
    return await _call_llm_json(
        prompt=prompt,
        prompt_vars={
            "contact_name": item.contact_name,
            "contact_email": item.contact_email,
            "contact_role": item.contact_role,
            "company_name": item.company_name,
            "company_domain": item.company_domain,
            "industry": item.industry,
            "company_size": item.company_size,
            "source_type": item.source_type,
            "source_name": item.source_name,
            "content_summary": item.content_summary,
            "intent_signals": ", ".join(item.intent_signals),
            "enrichment_summary": item.enrichment_summary,
            "score": str(item.score),
            "score_reasoning": item.score_reasoning,
            "recommended_action": item.recommended_action,
            "sales_memo": item.sales_memo,
            "sender_name": item.sender_name,
            "calendly_url": item.calendly_url,
        },
        span_name="crm-outbound-email",
        generation_name="deepseek-outbound-email",
        request=request,
        lead_id=item.lead_id,
        correlation_id=item.correlation_id,
        source_type=item.source_type,
        company_name=item.company_name,
        company_domain=item.company_domain,
        contact_role=item.contact_role,
        trace_input=build_crm_trace_input(
            lead_id=item.lead_id,
            correlation_id=item.correlation_id,
            source_type=item.source_type,
            contact_email=item.contact_email,
            company_name=item.company_name,
            raw_content=item.content_summary,
        ),
        result_model=OutboundEmailResult,
        fallback_factory=lambda: _fallback_outbound_email(
            contact_name=item.contact_name,
            company_name=item.company_name,
            content_summary=item.content_summary,
            sales_memo_raw=item.sales_memo,
            calendly_url=item.calendly_url,
        ),
    )


@app.post("/weekly-insights", response_model=WeeklyInsightsResult)
async def weekly_insights(item: WeeklyInsightsRequest, request: Request):
    prompt = load_prompt("weekly_insights")
    lead_id = f"weekly-{item.week_start}"
    metrics_json = json.dumps(item.metrics, ensure_ascii=False, default=str)
    prior_json = json.dumps(item.prior_week_metrics, ensure_ascii=False, default=str)
    return await _call_llm_json(
        prompt=prompt,
        prompt_vars={
            "week_start": item.week_start,
            "week_end": item.week_end,
            "metrics_json": metrics_json,
            "prior_week_metrics": prior_json,
        },
        span_name="crm-weekly-insights",
        generation_name="deepseek-weekly-insights",
        request=request,
        lead_id=lead_id,
        correlation_id=item.correlation_id or lead_id,
        source_type="weekly_report",
        company_name="",
        company_domain="",
        contact_role="",
        trace_input={
            "week_start": item.week_start,
            "week_end": item.week_end,
            "metrics_preview": truncate_for_llm(metrics_json, 4000),
            "prior_week_preview": truncate_for_llm(prior_json, 2000),
        },
        result_model=WeeklyInsightsResult,
        fallback_factory=lambda: _fallback_weekly_insights(item.metrics),
    )


@app.post("/manual-review", response_model=ManualReviewResult)
async def manual_review_explain(item: ManualReviewRequest, request: Request):
    prompt = load_prompt("manual_review")
    return await _call_llm_json(
        prompt=prompt,
        prompt_vars={
            "contact_name": item.contact_name,
            "contact_role": item.contact_role,
            "contact_email": item.contact_email,
            "company_name": item.company_name,
            "company_domain": item.company_domain,
            "score": str(item.score),
            "score_reasoning": item.score_reasoning,
            "enrichment_status": item.enrichment_status,
            "review_triggers": item.review_triggers,
        },
        span_name="crm-manual-review",
        generation_name="deepseek-manual-review",
        request=request,
        lead_id=item.lead_id,
        correlation_id=item.correlation_id,
        source_type="review",
        company_name=item.company_name,
        company_domain=item.company_domain,
        contact_role=item.contact_role,
        trace_input=build_crm_trace_input(
            lead_id=item.lead_id,
            correlation_id=item.correlation_id,
            source_type="review",
            contact_email=item.contact_email,
            company_name=item.company_name,
            raw_content=item.review_triggers,
        ),
        result_model=ManualReviewResult,
        fallback_factory=lambda: ManualReviewResult(
            review_explanation="Manual review required; LLM explanation unavailable",
            suggested_questions=["Verify company and role", "Confirm budget and timeline"],
            risk_flags=["llm_unavailable"],
            confidence="low",
        ),
    )


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "n8n-crm-ai-service", "version": SERVICE_VERSION}


@app.get("/prompts")
def list_prompt_versions():
    from prompt_loader import list_prompts

    return {
        key: {
            "version": load_prompt(key).version,
            "hash": load_prompt(key).prompt_hash,
        }
        for key in list_prompts()
    }
