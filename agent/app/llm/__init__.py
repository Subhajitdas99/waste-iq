"""LLM Intelligence Layer.

A provider-agnostic, repository-grounded reasoning layer used by the AI
Engineering Agent. The LLM is never allowed to fabricate repository facts:
prompts are built from retrieved evidence only, every provider response is
strictly validated, grounded against the evidence universe (unverifiable
claims are rejected), cached, and observed through telemetry.

See docs/architecture/LLM_INTELLIGENCE_LAYER.md for the full design.
"""

from __future__ import annotations

from app.llm.service import LLMService

__all__ = ["LLMService"]
