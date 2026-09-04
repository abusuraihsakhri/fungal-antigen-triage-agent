#!/usr/bin/env python3
"""
Fungal Antigen Triage Agent

Real implementation of:
- Beta-D-Glucan (BDG) interpretation with false positive awareness
- Galactomannan (GM) Index interpretation (serum and BAL)
- Cryptococcal Antigen (CrAg) interpretation
- Mannan/Anti-mannan for Candida infection
- Combined interpretation algorithms
- Pre-test probability assessment based on host factors

Uses only Python stdlib.
"""

import argparse
import csv
import json
import sys
from typing import Dict, List, Optional, Any

# ─── Beta-D-Glucan (BDG) Interpretation ──────────────────────────────────────

BDG_THRESHOLDS = {
    "negative": {"max": 59.9, "label": "Negative", "clinical_significance": "LOW"},
    "indeterminate": {"min": 60, "max": 79.9, "label": "Indeterminate", "clinical_significance": "MODERATE"},
    "positive": {"min": 80, "label": "Positive", "clinical_significance": "HIGH"},
}

BDG_FALSE_POSITIVE_FACTORS = {
    "hemodialysis": {"risk": "HIGH", "description": "Cellulose membranes used in hemodialysis"},
    "iv_immunoglobulin": {"risk": "HIGH", "description": "IV immunoglobulin (IVIG) administration"},
    "albumin": {"risk": "MODERATE", "description": "Human serum albumin administration"},
    "certain_antibiotics": {"risk": "MODERATE", "description": "Piperacillin-tazobactam, amoxicillin-clavulanate"},
    "piperacillin_tazobactam": {"risk": "MODERATE", "description": "Piperacillin-tazobactam antibiotic"},
    "amoxicillin_clavulanate": {"risk": "MODERATE", "description": "Amoxicillin-clavulanate antibiotic"},
    "gauze": {"risk": "HIGH", "description": "Surgical gauze or other glucan-containing materials"},
    "methylcellulose": {"risk": "HIGH", "description": "Methylcellulose-containing products"},
    "blood_products": {"risk": "LOW", "description": "Certain blood transfusion products"},
    "bacterial_infection": {"risk": "LOW", "description": "Certain bacterial infections (Pseudomonas)"},
    "mucositis": {"risk": "LOW", "description": "Severe mucositis with GI translocation"},
}


def interpret_bdg(value_pg_ml: float,
                   false_positive_factors: Optional[List[str]] = None) -> Dict[str, Any]:
    """Interpret Beta-D-Glucan result.

    Args:
        value_pg_ml: BDG value in pg/mL
        false_positive_factors: List of known false positive factors present

    Returns:
        Dict with interpretation, clinical significance, and recommendations
    """
    # Input validation
    if not isinstance(value_pg_ml, (int, float)):
        return {"error": "BDG value must be a number", "value": str(value_pg_ml)}
    if value_pg_ml < 0:
        return {"error": "BDG value cannot be negative", "value": value_pg_ml}
    if value_pg_ml > 10000:
        return {"error": "BDG value exceeds plausible physiological range (>10000 pg/mL)", "value": value_pg_ml}

    # Determine category
    if value_pg_ml < 60:
        category = "NEGATIVE"
        label = "Negative"
        significance = "LOW"
        interpretation = "BDG negative. Invasive fungal infection unlikely in appropriate clinical context."
    elif value_pg_ml < 80:
        category = "INDETERMINATE"
        label = "Indeterminate"
        significance = "MODERATE"
        interpretation = ("BDG indeterminate (60-79 pg/mL). Repeat testing recommended. "
                         "Correlate with clinical presentation and other diagnostics.")
    else:
        category = "POSITIVE"
        label = "Positive"
        significance = "HIGH"
        interpretation = ("BDG positive (>=80 pg/mL). Suggests invasive fungal infection. "
                         "Most commonly associated with invasive candidiasis or invasive aspergillosis. "
                         "Also positive in Pneumocystis jirovecii pneumonia.")

    # Check for false positive factors
    fp_present = []
    fp_risk = "NONE"
    if false_positive_factors:
        for factor in false_positive_factors:
            factor_key = factor.lower().replace(" ", "_").replace("-", "_")
            for known_factor, info in BDG_FALSE_POSITIVE_FACTORS.items():
                if known_factor in factor_key or factor_key in known_factor:
                    fp_present.append({
                        "factor": factor,
                        "risk": info["risk"],
                        "description": info["description"],
                    })
                    if info["risk"] == "HIGH":
                        fp_risk = "HIGH"
                    elif info["risk"] == "MODERATE" and fp_risk != "HIGH":
                        fp_risk = "MODERATE"

    # Adjust interpretation for false positives
    adjusted_significance = significance
    if fp_present and category == "POSITIVE":
        if fp_risk == "HIGH":
            adjusted_significance = "MODERATE"
            interpretation += (" WARNING: High-risk false positive factors present. "
                             "Result may be falsely positive. Repeat testing after "
                             "removing false positive source recommended.")
        elif fp_risk == "MODERATE":
            interpretation += (" NOTE: Moderate false positive risk factors present. "
                             "Interpret with caution.")

    result = {
        "test": "Beta-D-Glucan (BDG)",
        "value_pg_ml": value_pg_ml,
        "category": category,
        "label": label,
        "clinical_significance": adjusted_significance,
        "interpretation": interpretation,
        "false_positive_factors": fp_present,
        "false_positive_risk": fp_risk,
    }

    # Add alerts
    alerts = []
    if category == "POSITIVE" and fp_risk != "HIGH":
        alerts.append({
            "severity": "WARNING",
            "type": "BDG_POSITIVE",
            "message": f"BDG positive at {value_pg_ml} pg/mL",
            "recommendation": "Evaluate for invasive fungal infection. Consider blood cultures, "
                            "imaging, and site-specific fungal diagnostics.",
        })
    elif category == "POSITIVE" and fp_risk == "HIGH":
        alerts.append({
            "severity": "ADVISORY",
            "type": "BDG_POSITIVE_FALSE_POSITIVE_RISK",
            "message": f"BDG positive ({value_pg_ml} pg/mL) but high false positive risk",
            "recommendation": "Repeat BDG after removing false positive source. "
                            "Correlate with other fungal diagnostics.",
        })
    elif category == "INDETERMINATE":
        alerts.append({
            "severity": "ADVISORY",
            "type": "BDG_INDETERMINATE",
            "message": f"BDG indeterminate at {value_pg_ml} pg/mL",
            "recommendation": "Repeat BDG testing in 48-72 hours. Correlate clinically.",
        })

    result["alerts"] = alerts
    return result


# ─── Galactomannan (GM) Interpretation ───────────────────────────────────────

GM_THRESHOLDS = {
    "serum": {
        "negative": {"max": 0.49, "label": "Negative"},
        "indeterminate": {"min": 0.5, "max": 0.99, "label": "Indeterminate"},
        "positive": {"min": 1.0, "label": "Positive"},
    },
    "bal": {
        "negative": {"max": 0.69, "label": "Negative"},
        "positive": {"min": 0.7, "label": "Positive"},
    },
}

GM_FALSE_POSITIVE_FACTORS = {
    "piperacillin_tazobactam": {"risk": "HIGH", "description": "Common cause of false positive GM"},
    "amoxicillin_clavulanate": {"risk": "MODERATE", "description": "May cause false positive GM"},
    "plasmalyte": {"risk": "MODERATE", "description": "IV solutions containing gluconate"},
    "cyclophosphamide": {"risk": "LOW", "description": "Some chemotherapy agents"},
    "bifidobacterium": {"risk": "LOW", "description": "Certain gut bacteria (cross-reactivity)"},
    "aspergillus_colonization": {"risk": "MODERATE", "description": "Airway colonization without invasion"},
    "histoplasmosis": {"risk": "LOW", "description": "Histoplasma cross-reactivity"},
}


def interpret_gm(index_value: float,
                  specimen_type: str = "serum",
                  false_positive_factors: Optional[List[str]] = None) -> Dict[str, Any]:
    """Interpret Galactomannan Index result.

    Args:
        index_value: GM optical density index (ODI)
        specimen_type: 'serum' or 'bal'
        false_positive_factors: List of known false positive factors

    Returns:
        Dict with interpretation and clinical guidance
    """
    # Input validation
    if not isinstance(index_value, (int, float)):
        return {"error": "GM index must be a number", "value": str(index_value)}
    if index_value < 0:
        return {"error": "GM index cannot be negative", "value": index_value}
    if index_value > 100:
        return {"error": "GM index exceeds plausible range (>100 ODI)", "value": index_value}

    specimen_key = specimen_type.lower().strip()
    thresholds = GM_THRESHOLDS.get(specimen_key, GM_THRESHOLDS["serum"])

    # Determine category
    if specimen_key == "bal":
        if index_value < 0.7:
            category = "NEGATIVE"
            label = "Negative"
            significance = "LOW"
            interpretation = "BAL GM negative (<0.7). Invasive pulmonary aspergillosis unlikely."
        else:
            category = "POSITIVE"
            label = "Positive"
            significance = "HIGH"
            interpretation = ("BAL GM positive (>=0.7). Suggests invasive pulmonary aspergillosis. "
                            "BAL GM is more sensitive than serum GM for pulmonary disease.")
    else:  # serum
        if index_value < 0.5:
            category = "NEGATIVE"
            label = "Negative"
            significance = "LOW"
            interpretation = "Serum GM negative (<0.5). Invasive aspergillosis unlikely."
        elif index_value < 1.0:
            category = "INDETERMINATE"
            label = "Indeterminate"
            significance = "MODERATE"
            interpretation = ("Serum GM indeterminate (0.5-0.9). Repeat testing in 24-48 hours. "
                            "Consider BAL GM if pulmonary involvement suspected.")
        else:
            category = "POSITIVE"
            label = "Positive"
            significance = "HIGH"
            interpretation = ("Serum GM positive (>=1.0). Strongly suggests invasive aspergillosis. "
                            "Initiate antifungal therapy and pursue CT imaging.")

    # Check false positive factors
    fp_present = []
    fp_risk = "NONE"
    if false_positive_factors:
        for factor in false_positive_factors:
            factor_key = factor.lower().replace(" ", "_").replace("-", "_")
            for known_factor, info in GM_FALSE_POSITIVE_FACTORS.items():
                if known_factor in factor_key or factor_key in known_factor:
                    fp_present.append({
                        "factor": factor,
                        "risk": info["risk"],
                        "description": info["description"],
                    })
                    if info["risk"] == "HIGH":
                        fp_risk = "HIGH"
                    elif info["risk"] == "MODERATE" and fp_risk != "HIGH":
                        fp_risk = "MODERATE"

    adjusted_significance = significance
    if fp_present and category == "POSITIVE":
        if fp_risk == "HIGH":
            adjusted_significance = "MODERATE"
            interpretation += (" WARNING: High false positive risk (e.g., piperacillin-tazobactam). "
                             "Repeat after discontinuation of confounding agent.")

    result = {
        "test": "Galactomannan (GM)",
        "index_value": index_value,
        "specimen_type": specimen_key,
        "category": category,
        "label": label,
        "clinical_significance": adjusted_significance,
        "interpretation": interpretation,
        "false_positive_factors": fp_present,
        "false_positive_risk": fp_risk,
    }

    # Alerts
    alerts = []
    if category == "POSITIVE" and fp_risk != "HIGH":
        alerts.append({
            "severity": "WARNING",
            "type": "GM_POSITIVE",
            "message": f"GM positive ({index_value}) in {specimen_key}",
            "recommendation": "Evaluate for invasive aspergillosis. CT chest recommended. "
                            "Initiate antifungal therapy per IDSA aspergillosis guidelines.",
        })
    elif category == "INDETERMINATE":
        alerts.append({
            "severity": "ADVISORY",
            "type": "GM_INDETERMINATE",
            "message": f"GM indeterminate ({index_value}) in {specimen_key}",
            "recommendation": "Repeat GM in 24-48 hours. Consider BAL if not already obtained.",
        })

    result["alerts"] = alerts
    return result


# ─── Cryptococcal Antigen (CrAg) Interpretation ─────────────────────────────

def interpret_crag(
    positive: bool,
    titer: Optional[str] = None,
    specimen_type: str = "serum",
    csf_opening_pressure: Optional[float] = None,
) -> Dict[str, Any]:
    """Interpret Cryptococcal Antigen test result.

    Args:
        positive: Whether CrAg is positive
        titer: CrAg titer (e.g., '1:2', '1:128', '1:1024')
        specimen_type: 'serum' or 'csf'
        csf_opening_pressure: CSF opening pressure in cmH2O (if CSF specimen)

    Returns:
        Dict with interpretation and clinical guidance
    """
    # Input validation
    if not isinstance(positive, bool):
        return {"error": "CrAg positive flag must be boolean", "value": str(positive)}
    if csf_opening_pressure is not None and (not isinstance(csf_opening_pressure, (int, float)) or csf_opening_pressure < 0):
        return {"error": "CSF opening pressure must be a non-negative number", "value": csf_opening_pressure}
    if csf_opening_pressure is not None and csf_opening_pressure > 100:
        return {"error": "CSF opening pressure exceeds plausible range (>100 cmH2O)", "value": csf_opening_pressure}

    result = {
        "test": "Cryptococcal Antigen (CrAg)",
        "specimen_type": specimen_type,
        "positive": positive,
    }

    if not positive:
        result.update({
            "category": "NEGATIVE",
            "clinical_significance": "LOW",
            "interpretation": "CrAg negative. Cryptococcal infection unlikely. "
                            "Note: May be negative early in infection or in isolated CNS disease "
                            "with intact immune function.",
        })
        result["alerts"] = []
        return result

    # Positive result
    titer_value = None
    if titer:
        # Parse titer (e.g., '1:128' -> 128)
        parts = titer.replace("1:", "").replace("1/", "").strip()
        try:
            titer_value = int(parts)
        except ValueError:
            titer_value = None

    # Estimate disease burden from titer
    if titer_value:
        if titer_value >= 512:
            burden = "HIGH"
            burden_desc = "High antigen burden. Associated with disseminated disease and higher fungal burden."
        elif titer_value >= 64:
            burden = "MODERATE"
            burden_desc = "Moderate antigen burden."
        elif titer_value >= 8:
            burden = "LOW_TO_MODERATE"
            burden_desc = "Low-moderate antigen burden."
        else:
            burden = "LOW"
            burden_desc = "Low antigen burden. May represent early or localized infection."
    else:
        burden = "UNKNOWN"
        burden_desc = "Titer not provided; unable to estimate burden."

    # Clinical significance based on specimen type
    if specimen_type.lower() == "csf":
        significance = "CRITICAL"
        interpretation = ("CrAg positive in CSF confirms cryptococcal meningitis. "
                        "Requires urgent treatment with amphotericin B + flucytosine "
                        "induction therapy. Monitor and manage intracranial pressure.")
    else:
        significance = "HIGH"
        interpretation = ("Serum CrAg positive. Suggests cryptococcal infection. "
                        "If neurological symptoms present, perform lumbar puncture for CSF analysis "
                        "and CrAg testing. Consider disseminated disease.")

    # CSF opening pressure
    pressure_alert = None
    if csf_opening_pressure is not None:
        if csf_opening_pressure > 25:
            pressure_alert = {
                "severity": "CRITICAL",
                "type": "ELEVATED_OPENING_PRESSURE",
                "message": f"Elevated CSF opening pressure ({csf_opening_pressure} cmH2O)",
                "recommendation": "Therapeutic lumbar puncture to reduce pressure. "
                                "Serial LPs may be needed. Consider acetazolamide.",
            }

    result.update({
        "category": "POSITIVE",
        "clinical_significance": significance,
        "interpretation": interpretation,
        "titer": titer,
        "titer_value": titer_value,
        "disease_burden": burden,
        "disease_burden_description": burden_desc,
    })

    alerts = [{
        "severity": "CRITICAL" if specimen_type.lower() == "csf" else "WARNING",
        "type": "CRAG_POSITIVE",
        "message": f"CrAg positive in {specimen_type}" + (f" (titer: {titer})" if titer else ""),
        "recommendation": "Evaluate for cryptococcal disease. If CNS symptoms, perform LP. "
                        "Initiate antifungal therapy per IDSA guidelines.",
    }]

    if pressure_alert:
        alerts.append(pressure_alert)

    result["alerts"] = alerts
    return result


# ─── Mannan/Anti-mannan for Candida ──────────────────────────────────────────

def interpret_mannan(
    mannan_value: Optional[float] = None,
    anti_mannan_value: Optional[float] = None,
) -> Dict[str, Any]:
    """Interpret Mannan and Anti-mannan antibody results for Candida infection.

    Args:
        mannan_value: Mannan antigen value (pg/mL); positive >= 125 pg/mL (Platelia)
        anti_mannan_value: Anti-mannan antibody value (AU/mL); positive >= 10 AU/mL

    Returns:
        Dict with interpretation
    """
    # Input validation
    if mannan_value is not None and not isinstance(mannan_value, (int, float)):
        return {"error": "Mannan value must be a number", "value": str(mannan_value)}
    if anti_mannan_value is not None and not isinstance(anti_mannan_value, (int, float)):
        return {"error": "Anti-mannan value must be a number", "value": str(anti_mannan_value)}
    if mannan_value is not None and mannan_value < 0:
        return {"error": "Mannan value cannot be negative", "value": mannan_value}
    if anti_mannan_value is not None and anti_mannan_value < 0:
        return {"error": "Anti-mannan value cannot be negative", "value": anti_mannan_value}

    mannan_positive = mannan_value is not None and mannan_value >= 125
    anti_mannan_positive = anti_mannan_value is not None and anti_mannan_value >= 10

    result = {
        "test": "Mannan/Anti-mannan (Candida)",
        "mannan_value": mannan_value,
        "mannan_positive": mannan_positive,
        "anti_mannan_value": anti_mannan_value,
        "anti_mannan_positive": anti_mannan_positive,
    }

    if mannan_positive and anti_mannan_positive:
        result.update({
            "category": "BOTH_POSITIVE",
            "clinical_significance": "HIGH",
            "interpretation": "Both mannan antigen and anti-mannan antibodies positive. "
                            "High sensitivity for invasive candidiasis. Combined testing "
                            "improves sensitivity over individual tests.",
        })
    elif mannan_positive:
        result.update({
            "category": "MANNAN_POSITIVE",
            "clinical_significance": "MODERATE_TO_HIGH",
            "interpretation": "Mannan antigen positive. Suggests invasive Candida infection. "
                            "Anti-mannan antibodies negative may indicate early infection "
                            "or immunosuppression.",
        })
    elif anti_mannan_positive:
        result.update({
            "category": "ANTI_MANNAN_POSITIVE",
            "clinical_significance": "MODERATE",
            "interpretation": "Anti-mannan antibodies positive. May indicate current or recent "
                            "Candida infection. Mannan antigen negative may indicate clearance "
                            "or low fungal burden.",
        })
    else:
        result.update({
            "category": "BOTH_NEGATIVE",
            "clinical_significance": "LOW",
            "interpretation": "Both mannan and anti-mannan negative. Invasive candidiasis "
                            "unlikely, but does not completely exclude infection in "
                            "immunosuppressed patients.",
        })

    alerts = []
    if mannan_positive:
        alerts.append({
            "severity": "WARNING",
            "type": "MANNAN_POSITIVE",
            "message": "Mannan antigen positive - suggests invasive Candida infection",
            "recommendation": "Obtain blood cultures. Consider empiric antifungal therapy. "
                            "Evaluate for deep-seated candidiasis.",
        })

    result["alerts"] = alerts
    return result


# ─── Pre-test Probability Assessment ─────────────────────────────────────────

def assess_pretest_probability(
    host_factors: Dict[str, Any],
) -> Dict[str, Any]:
    """Assess pre-test probability of invasive fungal infection based on host factors.

    Args:
        host_factors: Dict with clinical risk factors:
            - neutropenic: bool (ANC < 500)
            - hematologic_malignancy: bool
            - solid_organ_transplant: bool
            - stem_cell_transplant: bool
            - prolonged_icu: bool (>7 days)
            - corticosteroids: bool (prolonged use)
            - broad_spectrum_antibiotics: bool (>4 days)
            - central_venous_catheter: bool
            - total_parenteral_nutrition: bool
            - abdominal_surgery: bool
            - candida_colonization: bool
            - hiv_aids: bool
            - liver_failure: bool

    Returns:
        Dict with pre-test probability and risk assessment
    """
    risk_score = 0
    risk_factors_present = []

    factor_weights = {
        "neutropenic": 3,
        "hematologic_malignancy": 3,
        "solid_organ_transplant": 3,
        "stem_cell_transplant": 3,
        "prolonged_icu": 2,
        "corticosteroids": 2,
        "broad_spectrum_antibiotics": 2,
        "central_venous_catheter": 1,
        "total_parenteral_nutrition": 2,
        "abdominal_surgery": 2,
        "candida_colonization": 2,
        "hiv_aids": 3,
        "liver_failure": 2,
    }

    for factor, weight in factor_weights.items():
        if host_factors.get(factor, False):
            risk_score += weight
            risk_factors_present.append({"factor": factor, "weight": weight})

    # Determine risk category
    if risk_score >= 8:
        risk_category = "HIGH"
        probability = "HIGH"
        recommendation = ("High pre-test probability for invasive fungal infection. "
                        "Consider empiric antifungal therapy. Order BDG and GM testing. "
                        "Consider CT imaging.")
    elif risk_score >= 4:
        risk_category = "MODERATE"
        probability = "MODERATE"
        recommendation = ("Moderate pre-test probability. Order fungal biomarkers (BDG, GM). "
                        "Monitor closely. Consider antifungal prophylaxis.")
    elif risk_score >= 1:
        risk_category = "LOW_MODERATE"
        probability = "LOW_MODERATE"
        recommendation = ("Low-moderate risk. Fungal biomarkers may be useful if "
                        "clinical suspicion arises. Standard monitoring.")
    else:
        risk_category = "LOW"
        probability = "LOW"
        recommendation = ("Low pre-test probability. Routine fungal screening not recommended "
                        "unless clinical deterioration occurs.")

    return {
        "risk_score": risk_score,
        "risk_category": risk_category,
        "pre_test_probability": probability,
        "risk_factors_present": risk_factors_present,
        "total_risk_factors": len(risk_factors_present),
        "recommendation": recommendation,
    }


# ─── Combined Interpretation ─────────────────────────────────────────────────

def combined_interpretation(
    bdg_value: Optional[float] = None,
    gm_index: Optional[float] = None,
    gm_specimen: str = "serum",
    crag_positive: Optional[bool] = None,
    mannan_value: Optional[float] = None,
    anti_mannan_value: Optional[float] = None,
    host_factors: Optional[Dict[str, Any]] = None,
    false_positive_factors: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Combined interpretation of multiple fungal antigen tests.

    Args:
        bdg_value: BDG value in pg/mL
        gm_index: GM index value
        gm_specimen: GM specimen type
        crag_positive: CrAg result
        mannan_value: Mannan value
        anti_mannan_value: Anti-mannan value
        host_factors: Host risk factors for pre-test probability
        false_positive_factors: Known false positive factors

    Returns:
        Comprehensive combined interpretation
    """
    results = {
        "tests_performed": [],
        "individual_results": {},
        "alerts": [],
    }

    # Pre-test probability
    if host_factors:
        pretest = assess_pretest_probability(host_factors)
        results["pretest_probability"] = pretest
        results["alerts"].extend([{
            "severity": "ADVISORY",
            "type": "PRETEST_PROBABILITY",
            "message": f"Pre-test probability: {pretest['risk_category']} (score: {pretest['risk_score']})",
            "recommendation": pretest["recommendation"],
        }])

    # BDG
    if bdg_value is not None:
        bdg_result = interpret_bdg(bdg_value, false_positive_factors)
        results["tests_performed"].append("BDG")
        results["individual_results"]["BDG"] = bdg_result
        results["alerts"].extend(bdg_result.get("alerts", []))

    # GM
    if gm_index is not None:
        gm_result = interpret_gm(gm_index, gm_specimen, false_positive_factors)
        results["tests_performed"].append("GM")
        results["individual_results"]["GM"] = gm_result
        results["alerts"].extend(gm_result.get("alerts", []))

    # CrAg
    if crag_positive is not None:
        crag_result = interpret_crag(crag_positive)
        results["tests_performed"].append("CrAg")
        results["individual_results"]["CrAg"] = crag_result
        results["alerts"].extend(crag_result.get("alerts", []))

    # Mannan/Anti-mannan
    if mannan_value is not None or anti_mannan_value is not None:
        mannan_result = interpret_mannan(mannan_value, anti_mannan_value)
        results["tests_performed"].append("Mannan/Anti-mannan")
        results["individual_results"]["Mannan"] = mannan_result
        results["alerts"].extend(mannan_result.get("alerts", []))

    # Combined algorithm
    positive_tests = []
    for test_name, test_result in results["individual_results"].items():
        cat = test_result.get("category", "")
        if cat in ("POSITIVE", "BOTH_POSITIVE", "MANNAN_POSITIVE", "ANTI_MANNAN_POSITIVE"):
            positive_tests.append(test_name)

    if len(positive_tests) >= 2:
        results["combined_interpretation"] = (
            f"Multiple positive fungal markers ({', '.join(positive_tests)}). "
            "High likelihood of invasive fungal infection. Initiate antifungal therapy "
            "and pursue definitive diagnostics."
        )
        results["combined_severity"] = "HIGH"
    elif len(positive_tests) == 1:
        results["combined_interpretation"] = (
            f"Single positive fungal marker ({positive_tests[0]}). "
            "Correlate with clinical presentation. Repeat testing or additional "
            "diagnostics recommended to confirm."
        )
        results["combined_severity"] = "MODERATE"
    else:
        results["combined_interpretation"] = (
            "All fungal markers negative or indeterminate. Invasive fungal infection "
            "unlikely in current testing. If clinical suspicion remains, repeat testing "
            "in 48-72 hours."
        )
        results["combined_severity"] = "LOW"

    return results


# ─── CLI ──────────────────────────────────────────────────────────────────────

def build_parser():
    """Build the argument parser."""
    p = argparse.ArgumentParser(
        prog="fungal-antigen-triage",
        description="Fungal Antigen Triage Agent"
    )
    sub = p.add_subparsers(dest="cmd")

    # BDG command
    s_bdg = sub.add_parser("bdg", help="Interpret Beta-D-Glucan")
    s_bdg.add_argument("--value", type=float, required=True, help="BDG value (pg/mL)")
    s_bdg.add_argument("--false-positives", nargs="*", help="Known false positive factors")

    # GM command
    s_gm = sub.add_parser("gm", help="Interpret Galactomannan")
    s_gm.add_argument("--index", type=float, required=True, help="GM index value")
    s_gm.add_argument("--specimen", default="serum", choices=["serum", "bal"])
    s_gm.add_argument("--false-positives", nargs="*", help="Known false positive factors")

    # CrAg command
    s_crag = sub.add_parser("crag", help="Interpret Cryptococcal Antigen")
    s_crag.add_argument("--positive", action="store_true", help="CrAg positive")
    s_crag.add_argument("--titer", help="CrAg titer (e.g., 1:128)")
    s_crag.add_argument("--specimen", default="serum", choices=["serum", "csf"])

    # Combined command
    s_combined = sub.add_parser("combined", help="Combined fungal antigen interpretation")
    s_combined.add_argument("--bdg", type=float, help="BDG value (pg/mL)")
    s_combined.add_argument("--gm", type=float, help="GM index")
    s_combined.add_argument("--gm-specimen", default="serum")
    s_combined.add_argument("--crag-positive", action="store_true")
    s_combined.add_argument("--mannan", type=float, help="Mannan value")
    s_combined.add_argument("--anti-mannan", type=float, help="Anti-mannan value")

    return p


def main(argv=None):
    """CLI entry point."""
    p = build_parser()
    args = p.parse_args(argv)

    if args.cmd == "bdg":
        result = interpret_bdg(args.value, args.false_positives)
        print(json.dumps(result, indent=2))
        return 0

    elif args.cmd == "gm":
        result = interpret_gm(args.index, args.specimen, args.false_positives)
        print(json.dumps(result, indent=2))
        return 0

    elif args.cmd == "crag":
        result = interpret_crag(args.positive, args.titer, args.specimen)
        print(json.dumps(result, indent=2))
        return 0

    elif args.cmd == "combined":
        result = combined_interpretation(
            bdg_value=args.bdg,
            gm_index=args.gm,
            gm_specimen=args.gm_specimen,
            crag_positive=args.crag_positive if args.crag_positive else None,
            mannan_value=args.mannan,
            anti_mannan_value=args.anti_mannan,
        )
        print(json.dumps(result, indent=2))
        return 0

    else:
        p.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
