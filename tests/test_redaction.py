from shopllm.redaction.engine import RedactionEngine
 
 
def test_redacts_email_and_phone():
    eng = RedactionEngine()
    text = "Contact Barbara at barbara@example.com or +33 6 12 34 56 78."
    r = eng.redact(text)
    assert "<​EMAIL>" in r.redacted_text
    assert "<​PHONE>" in r.redacted_text
    assert "barbara@example.com" not in r.redacted_text
    assert r.counts == {"EMAIL": 1, "PHONE_FR": 1}
 
 
def test_redacts_order_and_sku():
    eng = RedactionEngine()
    text = "My order ORD-12345 contains SKU-ABCD1234 and SKU_XYZ9876."
    r = eng.redact(text)
    assert r.counts.get("ORDER_ID", 0) == 1
    assert r.counts.get("SKU", 0) == 2
 
 
def test_redacts_credit_card_first():
    eng = RedactionEngine()
    text = "Card 4111 1111 1111 1111 used for ORD-99999."
    r = eng.redact(text)
    assert "<​CREDIT_CARD>" in r.redacted_text
    assert "4111" not in r.redacted_text
 
 
def test_no_pii_means_no_changes():
    eng = RedactionEngine()
    text = "Generate a punchy description for vegan sneakers."
    r = eng.redact(text)
    assert r.redacted_text == text
    assert r.total == 0
    