import re
from rapidfuzz import fuzz

REQUIRED_WARNING = (
    "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink "
    "alcoholic beverages during pregnancy because of the risk of birth defects. "
    "(2) Consumption of alcoholic beverages impairs your ability to drive a car or "
    "operate machinery, and may cause health problems."
)

def normalize_text(value: str) -> str:
    value = value or ""
    value = value.lower()
    value = re.sub(r"[^\w\s%./'-]", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def result(field, status, reason):
    return {"field": field, "status": status, "reason": reason}

def validate_flexible(field, expected, extracted):
    if not expected.strip():
        return result(field, "NEEDS REVIEW", "No expected value was entered.")
    expected_n = normalize_text(expected)
    extracted_n = normalize_text(extracted)
    if expected_n in extracted_n:
        return result(field, "MATCH", f'Expected value "{expected}" was detected on the label.')
    score = fuzz.partial_ratio(expected_n, extracted_n)
    if score >= 85:
        return result(field, "NEEDS REVIEW", f'Label text appears similar to "{expected}" but is not an exact normalized match.')
    return result(field, "MISMATCH", f'Expected value "{expected}" was not confidently detected.')

def validate_brand(expected, extracted):
    if not expected.strip():
        return result(
            "Brand Name",
            "NEEDS REVIEW",
            "No expected brand name was entered."
        )

    expected_n = normalize_text(expected)
    extracted_n = normalize_text(extracted)

    # Exact normalized match
    if expected_n in extracted_n:
        return result(
            "Brand Name",
            "MATCH",
            f'Expected brand "{expected}" was detected on the label.'
        )

    # Compare individual words because decorative label typography
    # may cause OCR to recognize only part of a brand name.
    expected_tokens = re.findall(r"[a-z0-9]+", expected_n)
    extracted_tokens = re.findall(r"[a-z0-9]+", extracted_n)

    matched_tokens = []

    for expected_token in expected_tokens:
        best_score = 0

        for extracted_token in extracted_tokens:
            score = fuzz.ratio(expected_token, extracted_token)
            best_score = max(best_score, score)

        if best_score >= 80:
            matched_tokens.append(expected_token)

    coverage = (
        len(matched_tokens) / len(expected_tokens)
        if expected_tokens else 0
    )

    if coverage == 1:
        return result(
            "Brand Name",
            "MATCH",
            f'All words in expected brand "{expected}" were detected.'
        )

    if coverage >= 0.60:
        return result(
            "Brand Name",
            "NEEDS REVIEW",
            f'Part of expected brand "{expected}" was detected, but OCR could not confidently verify the full brand name. Human review is recommended.'
        )

    return result(
        "Brand Name",
        "MISMATCH",
        f'Expected brand "{expected}" was not confidently detected.'
    )
def validate_class_type(expected, extracted):
    return validate_flexible("Class / Type", expected, extracted)

def _first_number(value):
    m = re.search(r"(\d+(?:\.\d+)?)", value or "")
    return float(m.group(1)) if m else None

def validate_abv(expected, extracted):
    if not expected.strip():
        return result("Alcohol Content", "NEEDS REVIEW", "No expected alcohol content was entered.")
    expected_num = _first_number(expected)
    detected = re.findall(r"(\d+(?:\.\d+)?)\s*%\s*(?:alc(?:ohol)?\.?\s*/?\s*vol\.?)?", extracted, flags=re.I)
    detected_nums = [float(x) for x in detected]
    if expected_num is None:
        return result("Alcohol Content", "NEEDS REVIEW", "Expected alcohol content could not be interpreted.")
    if any(abs(x - expected_num) < 0.01 for x in detected_nums):
        return result("Alcohol Content", "MATCH", f"{expected_num:g}% ABV was detected.")
    if detected_nums:
        return result("Alcohol Content", "MISMATCH", f"Expected {expected_num:g}% ABV; detected possible percentage value(s): {', '.join(f'{x:g}%' for x in detected_nums)}.")
    return result("Alcohol Content", "NEEDS REVIEW", "No reliable ABV percentage was detected in OCR text.")

def validate_net_contents(expected, extracted):
    if not expected.strip():
        return result("Net Contents", "NEEDS REVIEW", "No expected net contents were entered.")
    exp_num = _first_number(expected)
    exp_unit_match = re.search(r"\b(ml|mL|l|L|fl\.?\s*oz\.?)\b", expected)
    exp_unit = exp_unit_match.group(1).lower().replace(".", "").replace(" ", "") if exp_unit_match else None
    candidates = re.findall(r"(\d+(?:\.\d+)?)\s*(ml|mL|l|L|fl\.?\s*oz\.?)", extracted)
    normalized = [(float(n), u.lower().replace(".", "").replace(" ", "")) for n, u in candidates]
    if exp_num is not None and exp_unit and any(abs(n-exp_num) < 0.01 and u == exp_unit for n, u in normalized):
        return result("Net Contents", "MATCH", f'Expected net contents "{expected}" were detected.')
    if normalized:
        display = ", ".join(f"{n:g} {u}" for n, u in normalized)
        return result("Net Contents", "MISMATCH", f'Expected "{expected}"; detected possible value(s): {display}.')
    return result("Net Contents", "NEEDS REVIEW", "No reliable net-contents value was detected in OCR text.")

def validate_warning(extracted):
    text = normalize_text(extracted)
    required = normalize_text(REQUIRED_WARNING)
    if required in text:
        return result("Government Warning", "MATCH", "The required warning wording was detected in the OCR text. Visual formatting still requires human review.")
    score = fuzz.partial_ratio(required, text)
    if score >= 85:
        return result("Government Warning", "NEEDS REVIEW", "Most required warning wording appears present, but OCR did not confirm an exact text match. Human review is required.")
    if "government warning" in text:
        return result("Government Warning", "MISMATCH", "A government warning heading was detected, but the required warning text was not confirmed.")
    return result("Government Warning", "MISMATCH", "The required government warning was not detected.")
