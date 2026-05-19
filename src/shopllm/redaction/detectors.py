"""E-commerce-aware PII detectors. Regex-based, fast, zero ML dependency."""
from __future__ import annotations
 
import re
from dataclasses import dataclass
from typing import Pattern
 
 
@dataclass(frozen=True, slots=True)
class Detector:
    name: str          # e.g. "EMAIL", "PHONE_FR", "ORDER_ID"
    pattern: Pattern[str]
    placeholder: str   # e.g. "<​EMAIL>"
 
 
# Generic PII
EMAIL = Detector(
    name="EMAIL",
    pattern=re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    placeholder="<​EMAIL>",
)
PHONE_FR = Detector(
    name="PHONE_FR",
    pattern=re.compile(r"(?<!\w)(?:\+33|0)\s?[1-9](?:[\s.-]?\d{2}){4}\b"),
    placeholder="<​PHONE>",
)
PHONE_INTL = Detector(
    name="PHONE_INTL",
    pattern=re.compile(r"\+\d{1,3}[\s.-]?\d{1,4}[\s.-]?\d{3,4}[\s.-]?\d{3,4}"),
    placeholder="<​PHONE>",
)
IBAN = Detector(
    name="IBAN",
    pattern=re.compile(r"\b[A-Z]{2}\d{2}(?:[\s]?[A-Z0-9]{4}){2,7}[\s]?[A-Z0-9]{1,4}\b"),
    placeholder="<​IBAN>",
)
CREDIT_CARD = Detector(
    name="CREDIT_CARD",
    pattern=re.compile(r"\b(?:\d[ -]?){13,19}\b"),
    placeholder="<​CREDIT_CARD>",
)
 
# E-commerce specific
ORDER_ID = Detector(
    name="ORDER_ID",
    pattern=re.compile(r"\b(?:ORD|ORDER|CMD|PO)[-_]?\d{4,12}\b", re.IGNORECASE),
    placeholder="<​ORDER_ID>",
)
SKU = Detector(
    name="SKU",
    pattern=re.compile(r"\bSKU[-_]?[A-Z0-9]{4,16}\b", re.IGNORECASE),
    placeholder="<​SKU>",
)
TRACKING = Detector(
    name="TRACKING",
    pattern=re.compile(r"\b[A-Z]{2}\d{9}[A-Z]{2}\b"),  # postal/UPS-like
    placeholder="<​TRACKING>",
)
 
DEFAULT_DETECTORS: tuple[Detector, ...] = (
    CREDIT_CARD, IBAN, EMAIL, PHONE_FR, PHONE_INTL, ORDER_ID, TRACKING, SKU,
)