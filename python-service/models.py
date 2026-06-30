"""Pydantic models for CRM lead enrichment and scoring."""

from __future__ import annotations

from typing import List, Optional

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
