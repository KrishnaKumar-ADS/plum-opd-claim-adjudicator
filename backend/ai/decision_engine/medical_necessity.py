"""Medical necessity verification."""

from backend.ai.gemini_client import get_ai_client
from backend.ai.rag.retriever import retrieve_coverage_context
from backend.utils.logger import get_logger

logger = get_logger("medical_necessity")


def check_medical_necessity(diagnosis, treatments, medicines=None, test_results=None, prescription_details=None):
    checks = []
    rejection_codes = []

    basic_result = _basic_necessity_check(diagnosis, treatments)
    checks.extend(basic_result["checks"])

    ai_result = _ai_necessity_check(diagnosis, treatments, medicines or [], test_results or [])
    checks.append(ai_result)
    if not ai_result.get("passed", True):
        rejection_codes.append("NOT_MEDICALLY_NECESSARY")

    special_result = _check_special_categories(treatments)
    checks.extend(special_result["checks"])
    rejection_codes.extend(special_result.get("rejection_codes", []))

    return {"passed": len(rejection_codes) == 0, "checks": checks, "rejection_codes": rejection_codes, "step": "medical_necessity"}


def _basic_necessity_check(diagnosis, treatments):
    checks = []
    if not diagnosis or diagnosis.strip() == "":
        checks.append({"check": "diagnosis_present", "passed": False, "detail": "No diagnosis provided"})
        return {"checks": checks}
    checks.append({"check": "diagnosis_present", "passed": True, "detail": f"Diagnosis: {diagnosis}"})
    if not treatments:
        checks.append({"check": "treatment_present", "passed": False, "detail": "No treatments listed"})
    else:
        checks.append({"check": "treatment_present", "passed": True, "detail": f"Treatments: {', '.join(treatments)}"})
    return {"checks": checks}


def _ai_necessity_check(diagnosis, treatments, medicines, test_results):
    try:
        context = retrieve_coverage_context(", ".join(treatments), diagnosis)
        prompt = f"""You are a medical claims adjudicator. Evaluate medical necessity.
DIAGNOSIS: {diagnosis}
TREATMENTS: {', '.join(treatments)}
MEDICINES: {', '.join(medicines) if medicines else 'None'}
TESTS: {', '.join(test_results) if test_results else 'None'}
POLICY CONTEXT: {context if context else 'Standard OPD policy.'}

Guidelines:
1. Standard consultations and prescriptions for common acute illnesses (e.g., bronchitis, viral fever, gastroenteritis) with routine medicines (e.g., antibiotics, bronchodilators, paracetamol) are medically necessary.
2. Alternative medicine (Ayurveda, Homeopathy, Unani) is covered. Panchakarma therapy is a standard Ayurvedic treatment for chronic joint pain/arthritis, and is medically necessary when prescribed by an Ayurvedic practitioner (like Vaidya).
3. Do not reject standard GP consultations and prescriptions for common outpatient conditions.
4. If a claim contains a mix of medically necessary treatments (e.g. root canal) and cosmetic/excluded treatments (e.g. teeth whitening), return `medically_necessary: true`, but note the cosmetic/excluded items in `concerns`. A claim should only have `medically_necessary: false` if NONE of the treatments/procedures/medicines are medically necessary.

Respond ONLY with JSON:
{{"medically_necessary": true, "confidence": 0.95, "reasoning": "brief explanation", "concerns": []}}"""

        client = get_ai_client()
        result = client.generate_json(prompt, provider="groq")
        return {
            "check": "ai_medical_necessity", "passed": result.get("medically_necessary", True),
            "detail": result.get("reasoning", "AI evaluation completed"),
            "confidence": result.get("confidence", 0.8), "concerns": result.get("concerns", [])
        }
    except Exception as e:
        logger.error(f"AI medical necessity check failed: {e}")
        return {"check": "ai_medical_necessity", "passed": True, "detail": f"AI unavailable, defaulting to approved. Error: {e}", "confidence": 0.5}


def _check_special_categories(treatments):
    checks = []
    rejection_codes = []
    experimental_kw = ["experimental", "clinical trial", "investigational", "unproven"]
    cosmetic_kw = ["cosmetic", "aesthetic", "whitening", "botox", "filler", "liposuction"]

    all_cosmetic = True
    all_experimental = True
    has_treatments = len(treatments) > 0

    for t in treatments:
        tl = t.lower()
        is_experimental = any(kw in tl for kw in experimental_kw)
        is_cosmetic = any(kw in tl for kw in cosmetic_kw)

        if not is_experimental:
            all_experimental = False
        if not is_cosmetic:
            all_cosmetic = False

        if is_experimental:
            checks.append({"check": "experimental_treatment", "passed": False, "detail": f"'{t}' is experimental"})
        if is_cosmetic:
            checks.append({"check": "cosmetic_procedure", "passed": False, "detail": f"'{t}' is cosmetic"})

    if has_treatments:
        if all_experimental:
            rejection_codes.append("EXPERIMENTAL_TREATMENT")
        if all_cosmetic:
            rejection_codes.append("COSMETIC_PROCEDURE")

    if not checks:
        checks.append({"check": "special_categories", "passed": True, "detail": "No experimental/cosmetic treatments"})
    return {"checks": checks, "rejection_codes": rejection_codes}
