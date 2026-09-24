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
        return result(
            field,
            "NEEDS REVIEW",
            "No expected value was entered."
        )

    expected_n = normalize_text(expected)
    extracted_n = normalize_text(extracted)

    if expected_n in extracted_n:
        return result(
            field,
            "MATCH",
            f'Expected value "{expected}" was detected on the label.'
        )

    score = fuzz.partial_ratio(expected_n, extracted_n)

    if score >= 85:
        return result(
            field,
            "NEEDS REVIEW",
            f'Label text appears similar to "{expected}" but is not an exact normalized match.'
        )

    return result(
        field,
        "MISMATCH",
        f'Expected value "{expected}" was not confidently detected.'
    )


def validate_brand(expected, extracted):
    if not expected.strip():
        return result(
            "Brand Name",
            "NEEDS REVIEW",
            "No expected brand name was entered."
        )

    expected_n = normalize_text(expected)
    extracted_n = normalize_text(extracted)

    # Only return MATCH when the complete normalized brand
    # appears together in the OCR output.
    if expected_n in extracted_n:
        return result(
            "Brand Name",
            "MATCH",
            f'Expected brand "{expected}" was detected as a complete phrase.'
        )

    expected_tokens = re.findall(r"[a-z0-9]+", expected_n)
    extracted_tokens = re.findall(r"[a-z0-9]+", extracted_n)

    confirmed = []
    possible = []

    for expected_token in expected_tokens:
        # Exact token match
        if expected_token in extracted_tokens:
            confirmed.append(expected_token)
            continue

        # Allow limited fuzzy evidence only for longer words.
        # Fuzzy evidence can trigger NEEDS REVIEW, but never MATCH.
        if len(expected_token) > 3:
            best_score = 0

            for extracted_token in extracted_tokens:
                score = fuzz.ratio(expected_token, extracted_token)

                if score > best_score:
                    best_score = score

            if best_score >= 85:
                possible.append(expected_token)

    evidence_count = len(set(confirmed + possible))

    if len(expected_tokens) > 0:
        coverage = evidence_count / len(expected_tokens)
    else:
        coverage = 0

    if coverage >= 0.60:
        unverified = []

        for token in expected_tokens:
            if token not in confirmed and token not in possible:
                unverified.append(token)

        if unverified:
            missing_text = ", ".join(unverified).upper()

            reason = (
                f'OCR found partial evidence for expected brand "{expected}", '
                f'but could not confidently verify the complete brand. '
                f'Unverified word(s): {missing_text}. Human review is required.'
            )
        else:
            reason = (
                f'OCR detected the individual words in expected brand "{expected}", '
                f'but could not verify the complete brand as a phrase. '
                f'Human review is required.'
            )

        return result(
            "Brand Name",
            "NEEDS REVIEW",
            reason
        )

    return result(
        "Brand Name",
        "MISMATCH",
        f'Expected brand "{expected}" was not confidently detected.'
    )


def validate_class_type(expected, extracted):
    return validate_flexible(
        "Class / Type",
        expected,
        extracted
    )


def _first_number(value):
    m = re.search(r"(\d+(?:\.\d+)?)", value or "")

    if m:
        return float(m.group(1))

    return None


def validate_abv(expected, extracted):
    if not expected.strip():
        return result(
            "Alcohol Content",
            "NEEDS REVIEW",
            "No expected alcohol content was entered."
        )

    expected_num = _first_number(expected)

    detected = re.findall(
        r"(\d+(?:\.\d+)?)\s*%\s*(?:alc(?:ohol)?\.?\s*/?\s*vol\.?)?",
        extracted,
        flags=re.I
    )

    detected_nums = [float(x) for x in detected]

    if expected_num is None:
        return result(
            "Alcohol Content",
            "NEEDS REVIEW",
            "Expected alcohol content could not be interpreted."
        )

    if any(abs(x - expected_num) < 0.01 for x in detected_nums):
        return result(
            "Alcohol Content",
            "MATCH",
            f"{expected_num:g}% ABV was detected."
        )

    if detected_nums:
        detected_text = ", ".join(
            f"{x:g}%"
            for x in detected_nums
        )

        return result(
            "Alcohol Content",
            "MISMATCH",
            f"Expected {expected_num:g}% ABV; detected possible percentage value(s): {detected_text}."
        )

    return result(
        "Alcohol Content",
        "NEEDS REVIEW",
        "No reliable ABV percentage was detected in OCR text."
    )


def validate_net_contents(expected, extracted):
    if not expected.strip():
        return result(
            "Net Contents",
            "NEEDS REVIEW",
            "No expected net contents were entered."
        )

    exp_num = _first_number(expected)

    exp_unit_match = re.search(
        r"\b(ml|mL|l|L|fl\.?\s*oz\.?)\b",
        expected
    )

    if exp_unit_match:
        exp_unit = (
            exp_unit_match
            .group(1)
            .lower()
            .replace(".", "")
            .replace(" ", "")
        )
    else:
        exp_unit = None

    candidates = re.findall(
        r"(\d+(?:\.\d+)?)\s*(ml|mL|l|L|fl\.?\s*oz\.?)",
        extracted
    )

    normalized = []

    for number, unit in candidates:
        normalized.append(
            (
                float(number),
                unit.lower().replace(".", "").replace(" ", "")
            )
        )

    if exp_num is not None and exp_unit:
        for number, unit in normalized:
            if abs(number - exp_num) < 0.01 and unit == exp_unit:
                return result(
                    "Net Contents",
                    "MATCH",
                    f'Expected net contents "{expected}" were detected.'
                )

    if normalized:
        display = ", ".join(
            f"{number:g} {unit}"
            for number, unit in normalized
        )

        return result(
            "Net Contents",
            "MISMATCH",
            f'Expected "{expected}"; detected possible value(s): {display}.'
        )

    return result(
        "Net Contents",
        "NEEDS REVIEW",
        "No reliable net-contents value was detected in OCR text."
    )


def validate_warning(extracted):
    text = normalize_text(extracted)
    required = normalize_text(REQUIRED_WARNING)

    if required in text:
        return result(
            "Government Warning",
            "MATCH",
            "The required warning wording was detected in the OCR text. Visual formatting still requires human review."
        )

    score = fuzz.partial_ratio(required, text)

    if score >= 85:
        return result(
            "Government Warning",
            "NEEDS REVIEW",
            "Most required warning wording appears present, but OCR did not confirm an exact text match. Human review is required."
        )

    if "government warning" in text:
        return result(
            "Government Warning",
            "MISMATCH",
            "A government warning heading was detected, but the required warning text was not confirmed."
        )

    return result(
        "Government Warning",
        "MISMATCH",
        "The required government warning was not detected."
    )
