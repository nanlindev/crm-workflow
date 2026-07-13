"""Pydantic models for CRM lead enrichment and scoring."""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class EnrichmentRequest(BaseModel):
    lead_id: str
    correlation_id: str
    source_type: str = ""
    source_name: str = ""
    contact_name: str = ""
    contact_email: str = ""
    contact_role: str = ""
    company_name: str = ""
    company_domain: str = ""
    domain_type: str = "unknown"
    raw_content: str = ""
    external_enrichment: str = ""


class EnrichmentResult(BaseModel):
    content_summary: str = ""
    industry: str = ""
    company_size: str = ""
    intent_signals: List[str] = Field(default_factory=list)
    enrichment_summary: str = ""


class ScoringRequest(BaseModel):
    lead_id: str
    correlation_id: str
    source_type: str = ""
    source_name: str = ""
    source_trust_level: int = 50
    contact_name: str = ""
    contact_email: str = ""
    contact_role: str = ""
    company_name: str = ""
    company_domain: str = ""
    industry: str = ""
    company_size: str = ""
    content_summary: str = ""
    intent_signals: List[str] = Field(default_factory=list)
    enrichment_status: str = "pending"
    enrichment_summary: str = ""


class ScoringResult(BaseModel):
    score: int = Field(ge=0, le=100)
    score_reasoning: str = ""
    confidence: str = "medium"
    recommended_action: str = "manual_review"
    intent_signals: List[str] = Field(default_factory=list)
    routing_decision: str = ""
    fallback_used: bool = False


class ManualReviewRequest(BaseModel):
    lead_id: str
    correlation_id: str
    contact_name: str = ""
    contact_role: str = ""
    contact_email: str = ""
    company_name: str = ""
    company_domain: str = ""
    score: int = 0
    score_reasoning: str = ""
    enrichment_status: str = ""
    review_triggers: str = ""


class ManualReviewResult(BaseModel):
    review_explanation: str = ""
    suggested_questions: List[str] = Field(default_factory=list)
    risk_flags: List[str] = Field(default_factory=list)
    confidence: str = "medium"


class SalesMemoRequest(BaseModel):
    lead_id: str
    correlation_id: str
    source_type: str = ""
    source_name: str = ""
    contact_name: str = ""
    contact_email: str = ""
    contact_role: str = ""
    company_name: str = ""
    company_domain: str = ""
    industry: str = ""
    company_size: str = ""
    content_summary: str = ""
    intent_signals: List[str] = Field(default_factory=list)
    enrichment_summary: str = ""
    score: int = Field(default=0, ge=0, le=100)
    score_reasoning: str = ""
    recommended_action: str = ""


class SalesMemoResult(BaseModel):
    company_background: List[str] = Field(default_factory=list)
    talking_points: List[str] = Field(default_factory=list)
    pain_hypotheses: List[str] = Field(default_factory=list)
    recommended_opener: str = ""
    fallback_used: bool = False


class OutboundEmailRequest(BaseModel):
    lead_id: str
    correlation_id: str
    source_type: str = ""
    source_name: str = ""
    contact_name: str = ""
    contact_email: str = ""
    contact_role: str = ""
    company_name: str = ""
    company_domain: str = ""
    industry: str = ""
    company_size: str = ""
    content_summary: str = ""
    intent_signals: List[str] = Field(default_factory=list)
    enrichment_summary: str = ""
    score: int = Field(default=0, ge=0, le=100)
    score_reasoning: str = ""
    recommended_action: str = ""
    sales_memo: str = ""
    sender_name: str = ""
    calendly_url: str = ""


class OutboundEmailResult(BaseModel):
    subject: str = ""
    body: str = ""
    personalization_notes: str = ""
    fallback_used: bool = False


class WeeklyInsightsRequest(BaseModel):
    week_start: str
    week_end: str
    correlation_id: str = ""
    metrics: dict[str, Any] = Field(default_factory=dict)
    prior_week_metrics: dict[str, Any] = Field(default_factory=dict)


class WeeklyInsightsResult(BaseModel):
    executive_summary: str = ""
    key_trends: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    anomalies: List[str] = Field(default_factory=list)
    fallback_used: bool = False
