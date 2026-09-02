# Fungal Antigen Triage Agent

> **Domain:** Infectious Disease Surveillance & Microbiology  
> **Reference Guidelines & Standards:** `CLSI M100, EUCAST & CDC NHSN Clinical Standards`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Fungal Antigen Triage Agent** is an advanced analytical and computational platform implementing Galactomannan, Beta-D-Glucan & Cryptococcal Antigen Arbiter.

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`interpret_bdg()`**: Interpret Beta-D-Glucan result.

Args:
    value_pg_ml: BDG value in pg/mL
    false_positive_factors: List of known false positive factors present

Returns:
    Dict with interpretation, clinical significance, and recommendations
- **`interpret_gm()`**: Interpret Galactomannan Index result.

Args:
    index_value: GM optical density index (ODI)
    specimen_type: 'serum' or 'bal'
    false_positive_factors: List of known false positive factors

Returns:
    Dict with interpretation and clinical guidance
- **`interpret_crag()`**: Interpret Cryptococcal Antigen test result.

Args:
    positive: Whether CrAg is positive
    titer: CrAg titer (e.g., '1:2', '1:128', '1:1024')
    specimen_type: 'serum' or 'csf'
    csf_opening_pressure: CSF opening pressure in cmH2O (if CSF specimen)

Returns:
    Dict with interpretation and clinical guidance
- **`interpret_mannan()`**: Interpret Mannan and Anti-mannan antibody results for Candida infection.

Args:
    mannan_value: Mannan antigen value (pg/mL); positive >= 125 pg/mL (Platelia)
    anti_mannan_value: Anti-mannan antibody value (AU/mL); positive >= 10 AU/mL

Returns:
    Dict with interpretation
- **`assess_pretest_probability()`**: Assess pre-test probability of invasive fungal infection based on host factors.

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

---

## 📐 Mathematical Formulation & Logic

```text
  fp_risk = "NONE"
  fp_risk = "HIGH"
  fp_risk = "MODERATE"
  if fp_risk == "HIGH":
  elif fp_risk == "MODERATE":
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --input data.csv
```

### Parameter Reference
- `--interactive`: Launch guided terminal interactive wizard.
- `--input <path>`: Evaluate input from JSON or CSV specification.
- `--json`: Output deterministic structured results in JSON format.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `case_id` | Parameter / observation metric | Required |
| `patient_synthetic_id` | Parameter / observation metric | Required |
| `metric_primary` | Parameter / observation metric | Required |
| `metric_secondary` | Parameter / observation metric | Required |
| `is_stat` | Parameter / observation metric | Required |
| `status_flag` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t fungal-antigen-triage-agent .
docker run -p 8000:8000 fungal-antigen-triage-agent
```
