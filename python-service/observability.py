import hashlib
import json
import time
from typing import Any, Mapping, Optional

from opentelemetry import context
from opentelemetry.propagate import extract

LLM_CONTENT_LIMIT = 3000
METADATA_PREVIEW_LIMIT = 200
SUMMARY_PREVIEW_LIMIT = 300


def preview(text: str | None, n: int = METADATA_PREVIEW_LIMIT) -> str:
    text = (text or "").strip()
    return text if len(text) <= n else text[: n - 3] + "..."


def content_hash(text: str | None) -> str:
    return hashlib.sha256((text or "").encode()).hexdigest()[:16]


def truncate_for_llm(content: str | None, limit: int = LLM_CONTENT_LIMIT) -> tuple[str, bool]:
    content = content or ""
    if len(content) <= limit:
        return content, False
    return content[:limit], True


def build_crm_trace_input(
    *,
    lead_id: str,
    correlation_id: str,
    source_type: str,
    contact_email: str,
    company_name: str,
    raw_content: str | None,
) -> dict[str, Any]:
    return {
        "lead_id": lead_id,
        "correlation_id": correlation_id,
        "source_type": source_type,
        "contact_email": preview(contact_email, 80),
        "company_name": preview(company_name, 120),
        "content_preview": preview(raw_content),
        "content_length": len(raw_content or ""),
    }


def build_enrichment_trace_output(result: dict[str, Any]) -> dict[str, Any]:
    signals = result.get("intent_signals") or []
    return {
        "content_summary": preview(result.get("content_summary", ""), SUMMARY_PREVIEW_LIMIT),
        "industry": result.get("industry"),
        "company_size": result.get("company_size"),
        "intent_signals": signals[:5],
        "enrichment_summary": preview(result.get("enrichment_summary", ""), SUMMARY_PREVIEW_LIMIT),
    }


def build_scoring_trace_output(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "score": result.get("score"),
        "score_reasoning": preview(result.get("score_reasoning", ""), SUMMARY_PREVIEW_LIMIT),
        "confidence": result.get("confidence"),
        "recommended_action": result.get("recommended_action"),
        "routing_decision": preview(result.get("routing_decision", ""), SUMMARY_PREVIEW_LIMIT),
        "fallback_used": result.get("fallback_used", False),
    }


def build_crm_propagate_metadata(
    *,
    lead_id: str,
    correlation_id: str,
    source_type: str,
    company_name: str,
    company_domain: str,
    contact_role: str,
    score: int | None = None,
    score_reasoning: str | None = None,
    recommended_action: str | None = None,
    model_name: str,
    prompt_version: str,
    prompt_hash_value: str,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    latency_ms: int | None = None,
    confidence: str | None = None,
    enrichment_summary: str | None = None,
    routing_decision: str | None = None,
    error_flag: bool = False,
) -> dict[str, str]:
    meta: dict[str, str] = {
        "lead_id": lead_id,
        "correlation_id": correlation_id,
        "source_type": source_type or "",
        "company_name": preview(company_name, 120),
        "company_domain": preview(company_domain, 80),
        "contact_role": preview(contact_role, 80),
        "model_name": model_name,
        "prompt_version": prompt_version,
        "prompt_hash": prompt_hash_value,
        "error_flag": str(error_flag).lower(),
    }
    if score is not None:
        meta["score"] = str(score)
    if score_reasoning:
        meta["score_reasoning"] = preview(score_reasoning, SUMMARY_PREVIEW_LIMIT)
    if recommended_action:
        meta["recommended_action"] = recommended_action
    if input_tokens is not None:
        meta["input_tokens"] = str(input_tokens)
    if output_tokens is not None:
        meta["output_tokens"] = str(output_tokens)
    if latency_ms is not None:
        meta["latency_ms"] = str(latency_ms)
    if confidence:
        meta["confidence"] = confidence
    if enrichment_summary:
        meta["enrichment_summary"] = preview(enrichment_summary, SUMMARY_PREVIEW_LIMIT)
    if routing_decision:
        meta["routing_decision"] = preview(routing_decision, SUMMARY_PREVIEW_LIMIT)
    return meta


def build_failed_trace_output(error_type: str, error_stage: str) -> dict[str, str]:
    return {
        "status": "failed",
        "error_type": error_type,
        "error_stage": error_stage,
    }


def classify_exception(exc: Exception) -> tuple[str, str, int]:
    if isinstance(exc, json.JSONDecodeError):
        return "json_parse_error", "parse", 502
    if isinstance(exc, ValueError) and "Empty response" in str(exc):
        return "empty_response", "llm_call", 502
    if "status_code" in dir(exc):
        return "provider_error", "llm_call", 502
    return "internal_error", "unknown", 500


def _headers_to_carrier(headers: Mapping[str, str]) -> dict[str, str]:
    return {k.lower(): v for k, v in headers.items()}


def get_correlation_id_from_headers(headers: Mapping[str, str]) -> str | None:
    carrier = _headers_to_carrier(headers)
    return carrier.get("x-correlation-id") or carrier.get("correlation-id")


def build_trace_context_from_headers(headers: Mapping[str, str]) -> Optional[dict[str, str]]:
    traceparent = _headers_to_carrier(headers).get("traceparent")
    if not traceparent:
        return None

    parts = traceparent.split("-")
    if len(parts) != 4 or parts[0] != "00":
        return None

    trace_id, parent_span_id, flags = parts[1], parts[2], parts[3]
    if len(trace_id) != 32 or len(parent_span_id) != 16:
        return None
    if flags not in {"00", "01"}:
        return None

    return {
        "trace_id": trace_id.lower(),
        "parent_span_id": parent_span_id.lower(),
    }


def attach_incoming_trace_context(headers: Mapping[str, str]):
    carrier = _headers_to_carrier(headers)
    if "traceparent" not in carrier:
        return None
    return context.attach(extract(carrier))


def detach_trace_context(token) -> None:
    if token is not None:
        context.detach(token)


class LatencyTracker:
    def __init__(self) -> None:
        self._start = time.perf_counter()

    @property
    def latency_ms(self) -> int:
        return int((time.perf_counter() - self._start) * 1000)
