"""Redaction engine: applies detectors, produces a redacted text + audit report."""
from __future__ import annotations
 
from dataclasses import dataclass, field
from typing import Iterable
 
from shopllm.redaction.detectors import DEFAULT_DETECTORS, Detector
 
 
@dataclass(slots=True)
class RedactionHit:
    detector: str
    placeholder: str
    start: int
    end: int
 
 
@dataclass(slots=True)
class RedactionReport:
    redacted_text: str
    hits: list[RedactionHit] = field(default_factory=list)
 
    @property
    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for h in self.hits:
            out[h.detector] = out.get(h.detector, 0) + 1
        return out
 
    @property
    def total(self) -> int:
        return len(self.hits)
 
 
class RedactionEngine:
    def __init__(self, detectors: Iterable[Detector] = DEFAULT_DETECTORS) -> None:
        self._detectors = tuple(detectors)
 
    def redact(self, text: str) -> RedactionReport:
        hits: list[RedactionHit] = []
        redacted = text
        # Apply most-specific (financial) first; detectors list is already ordered.
        for det in self._detectors:
            def _replace(match: "re.Match[str]") -> str:
                hits.append(
                    RedactionHit(
                        detector=det.name,
                        placeholder=det.placeholder,
                        start=match.start(),
                        end=match.end(),
                    )
                )
                return det.placeholder
            redacted = det.pattern.sub(_replace, redacted)
        return RedactionReport(redacted_text=redacted, hits=hits)
    