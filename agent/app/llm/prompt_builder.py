"""Prompt construction for LLM calls.

Prompts are built exclusively from retrieved evidence — repository context and
review findings — never from the whole repository. Every prompt is redacted so
secrets that leaked into evidence snippets cannot reach the provider.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.llm.grounding import EvidenceEntry, build_evidence_entries
from app.llm.models import LLMRole, LLMRequest
from app.review.review_models import RepositoryContext, ReviewFinding

_CHARS_PER_TOKEN = 4.0

_PASSWORD_ASSIGNMENT = (
    r"(?i)\b(password|passwd|pwd|secret|api[_-]?key|token)\s*[=:]\s*" r"[^\s,;]{6,}"
)

_REDACTION_PATTERNS: list[tuple[str, str]] = [
    (
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
        "[REDACTED:PRIVATE-KEY]",
    ),
    (
        r"-----BEGIN OPENSSH PRIVATE KEY-----.*?-----END OPENSSH PRIVATE KEY-----",
        "[REDACTED:PRIVATE-KEY]",
    ),
    (r"\bBearer\s+[A-Za-z0-9._~+/=-]{12,}", "[REDACTED:BEARER]"),
    (r"\bgh[pousr]_[A-Za-z0-9]{20,}\b", "[REDACTED:GITHUB-TOKEN]"),
    (r"\bsk-[A-Za-z0-9_-]{16,}\b", "[REDACTED:API-KEY]"),
    (r"\bAKIA[0-9A-Z]{16}\b", "[REDACTED:AWS-KEY]"),
    (r"\bAIza[0-9A-Za-z_-]{20,}\b", "[REDACTED:GOOGLE-KEY]"),
    (_PASSWORD_ASSIGNMENT, "\\1=[REDACTED]"),
    (r"(?i)\bsession[_-]?id\s*[=:]\s*[^\s,;\"']{8,}", "session_id=[REDACTED]"),
    (r"(?i)(authorization|proxy-authorization|x-api-key)\s*:\s*[^\s]+", "\\1: [REDACTED]"),
    (r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b", "[REDACTED:JWT]"),
]

_SECRET_WORDS = re.compile(
    r"(?i)(BEGIN PRIVATE KEY|ssh-rsa|ssh-ed25519|aws_access_key|aws_secret_access_key|"
    r"client_secret|private key)"
)


@dataclass
class BuiltPrompts:
    system_prompt: str
    user_prompt: str
    evidence: list[EvidenceEntry]
    redactions: int


class Redactor:
    """Scrubs known secret shapes from any text before it enters a prompt."""

    def __init__(self, patterns: list[tuple[str, str]] | None = None) -> None:
        self._patterns = [
            (re.compile(pattern, re.DOTALL), replacement)
            for pattern, replacement in (patterns or _REDACTION_PATTERNS)
        ]

    def redact(self, text: str | None) -> str:
        if not text:
            return ""
        for pattern, replacement in self._patterns:
            text = pattern.sub(replacement, text)
        return text

    def count(self, text: str | None) -> int:
        """Number of secret-shaped fragments found in the text."""
        if not text:
            return 0
        return sum(len(pattern.findall(text)) for pattern, _ in self._patterns)


def _estimate_tokens(text: str) -> int:
    return max(1, round(len(text) / _CHARS_PER_TOKEN))


def _cap(text: str, max_tokens: int) -> str:
    """Truncate to an approximate token budget, preserving the head."""
    if _estimate_tokens(text) <= max_tokens:
        return text
    limit = int(max(1, max_tokens * _CHARS_PER_TOKEN))
    return text[:limit] + "\n[truncated]" + "\n"


_SYSTEM_TEMPLATE = """\
You are the Waste-IQ AI Engineering Agent's repository-grounding reasoner.

You are an assistant, not a decision maker. You explain, summarize, prioritize
and classify repository evidence; you never invent repository facts.

Hard rules:
1. Every claim you make MUST reference at least one evidence entry listed in
   the EVIDENCE section of the prompt. Never reference files, lines, ADRs,
   docs or roadmap items that are not listed there.
2. Do not mention evidence identifiers that were not supplied.
3. Do not fabricate paths, line numbers, or repository contents.
4. Do not approve, merge, or change anything. You only reason.
5. Never repeat secrets; redact anything secret-shaped as [REDACTED].
6. Return ONLY a single JSON object. No markdown fences, no commentary.
7. The JSON object MUST conform exactly to this schema:
{json_schema}

Role instruction: {role_instruction}
"""

_ANALYZE_INSTRUCTION = """\
You are analyzing the review findings below against the retrieved repository
context. Produce an analysis with:
- "summary": 1-4 sentences tying the findings to the evidence,
- "priorities": ordered list of what a human should address first,
- "recommendations": concrete next steps grounded in the evidence,
- "risks": consequences if ignored, each grounded in evidence,
- "confidence": 0..1
- "references": evidence entries that support the analysis.
"""

_EXPLAIN_INSTRUCTION = """\
You are explaining repository behavior or a review finding in answer to the
user's question. Produce:
- "explanation": a clear, evidence-grounded answer,
- "confidence": 0..1
- "references": evidence entries that support the explanation.
"""

_SUMMARIZE_INSTRUCTION = """\
You are summarizing a review (findings + repository context). Produce:
- "overview": 1-3 sentence summary grounded in evidence,
- "key_points": bullet-style key points, each grounded in evidence,
- "confidence": 0..1
- "references": evidence entries that support the summary.
"""

_ANALYZE_SCHEMA = """\
{"summary": "string", "priorities": ["string"], "recommendations": ["string"],
 "risks": ["string"], "confidence": 0.0, "references": [
   {"file_path": "string", "start_line": 1, "end_line": 2,
    "evidence_id": "code:path:line", "chunk_id": "chunk:path:line"}]}"""

_EXPLAIN_SCHEMA = """\
{"explanation": "string", "confidence": 0.0, "references": [
  {"file_path": "string", "start_line": 1, "end_line": 2,
   "evidence_id": "code:path:line", "chunk_id": "chunk:path:line"}]}"""

_SUMMARIZE_SCHEMA = """\
{"overview": "string", "key_points": ["string"], "confidence": 0.0, "references": [
  {"file_path": "string", "start_line": 1, "end_line": 2,
   "evidence_id": "code:path:line", "chunk_id": "chunk:path:line"}]}"""


def _finding_block(finding: ReviewFinding) -> str:
    lines = [
        f"- [{finding.rule_id}] ({finding.category}/{finding.severity}) "
        f"{finding.title} — {finding.explanation}",
        f"  evidence: {finding.reference}",
    ]
    if finding.snippet:
        snippet = "\n".join("  | " + line for line in finding.snippet.splitlines()[:6])
        lines.append(snippet)
    return "\n".join(lines)


def _evidence_block(entries: list[EvidenceEntry], redactor: Redactor, max_tokens: int) -> str:
    lines: list[str] = []
    budget = max_tokens
    for entry in entries:
        line = (
            f"- evidence_id: {entry.evidence_id} | chunk_id: {entry.chunk_id} | "
            f"file: {entry.path} | lines: {entry.start_line or 1}-{entry.end_line or 1} | "
            f"source: {entry.source_type}"
        )
        if entry.snippet:
            snippet = redactor.redact(entry.snippet)
            snippet = _cap(snippet, max(64, int(budget / max(1, len(entries) - len(lines)))))
            line = line + "\n" + "\n".join("  | " + s for s in snippet.splitlines()[:4])
        lines.append(line)
    return "\n".join(lines)


def _context_summary(context: RepositoryContext | None) -> str:
    if context is None:
        return "no repository context supplied"
    parts = [
        f"related files: {len(context.related_files)}",
        f"docs: {len(context.related_docs)}",
        f"adrs: {len(context.related_adrs)}",
        f"roadmap: {len(context.related_roadmap)}",
        f"similar code: {len(context.similar_code)}",
        f"known test files: {len(context.test_files_known)}",
    ]
    return ", ".join(parts)


class PromptBuilder:
    """Builds grounded, redacted prompts for a given role."""

    def __init__(
        self,
        *,
        redactor: Redactor | None = None,
        max_input_tokens: int = 14000,
        max_evidence_tokens: int = 9000,
    ) -> None:
        self._redactor = redactor or Redactor()
        self._max_input_tokens = max_input_tokens
        self._max_evidence_tokens = max_evidence_tokens

    def build(
        self,
        role: LLMRole,
        request: LLMRequest,
        *,
        findings: list[ReviewFinding] | None = None,
        context: RepositoryContext | None = None,
    ) -> BuiltPrompts:
        findings = request.findings if findings is None else findings
        context = request.context if context is None else context
        evidence = build_evidence_entries(findings, context)

        instruction = {
            "analyze": _ANALYZE_INSTRUCTION,
            "explain": _EXPLAIN_INSTRUCTION,
            "summarize": _SUMMARIZE_INSTRUCTION,
        }[role]
        schema = {
            "analyze": _ANALYZE_SCHEMA,
            "explain": _EXPLAIN_SCHEMA,
            "summarize": _SUMMARIZE_SCHEMA,
        }[role]
        system_prompt = _SYSTEM_TEMPLATE.format(json_schema=schema, role_instruction=instruction)

        sections: list[str] = [
            f"# Repository: {request.repository}",
            f"# Role: {role}",
            f"# Context: {_context_summary(context)}",
        ]
        if request.question:
            sections.append(f"# Question:\n{self._redactor.redact(request.question)}")
        if request.rules_used:
            sections.append(f"# Rules applied: {', '.join(sorted(request.rules_used))}")
        if findings:
            finding_lines = [self._redactor.redact(_finding_block(f)) for f in findings]
            sections.append("# Review findings:\n" + "\n".join(finding_lines))
        sections.append(
            "# EVIDENCE (the only files/lines you may reference):\n"
            + _evidence_block(evidence, self._redactor, self._max_evidence_tokens)
        )

        user_prompt = "\n\n".join(sections)
        redactions = (
            self._redactor.count(request.question)
            + sum(self._redactor.count(_finding_block(f)) for f in findings)
            + sum(self._redactor.count(e.snippet) for e in evidence if e.snippet)
        )
        user_prompt = _cap(user_prompt, self._max_input_tokens)
        return BuiltPrompts(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            evidence=evidence,
            redactions=redactions,
        )
