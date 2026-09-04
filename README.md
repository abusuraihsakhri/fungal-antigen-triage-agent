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

**Fungal Antigen Triage Agent** is an advanced analytical and computational platform implementing Galactomannan, Beta-D-Glucan & Cryptococcal Antigen Arbiter. It provides clinical decision support for interpreting fungal biomarker results in the context of invasive fungal infections.

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`interpret_bdg()`**: Interpret Beta-D-Glucan result with false positive awareness
- **`interpret_gm()`**: Interpret Galactomannan Index result (serum and BAL specimens)
- **`interpret_crag()`**: Interpret Cryptococcal Antigen test result with disease burden estimation
- **`interpret_mannan()`**: Interpret Mannan and Anti-mannan antibody results for Candida infection
- **`assess_pretest_probability()`**: Assess pre-test probability of invasive fungal infection based on host factors
- **`combined_interpretation()`**: Comprehensive combined interpretation of multiple fungal antigen tests

### 🛡️ Enterprise Security Features

- **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers
- **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation
- **PHI Redaction:** Automatic redaction of sensitive identifiers in output

### 🤖 Multi-Agent Architecture

- **InvariantQCWorker:** Primary metric threshold monitoring
- **SafetyEscalationWorker:** Critical safety interlock detection
- **ProtocolConformanceWorker:** Spec conformance and anomaly detection
- **SystemSupervisor:** Master orchestrator with consensus building

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/fungal-antigen-triage-agent.git
cd fungal-antigen-triage-agent

# Install dependencies
pip install fastapi uvicorn pydantic pytest
```

---

## 🚀 CLI Quickstart & Usage

### 1. Interpret Beta-D-Glucan
```bash
python cli.py bdg --value 150.0
python cli.py bdg --value 150.0 --false-positives hemodialysis iv_immunoglobulin
```

### 2. Interpret Galactomannan
```bash
python cli.py gm --index 1.5 --specimen serum
python cli.py gm --index 0.8 --specimen bal
python cli.py gm --index 1.5 --false-positives piperacillin_tazobactam
```

### 3. Interpret Cryptococcal Antigen
```bash
python cli.py crag --positive --titer 1:128 --specimen serum
python cli.py crag --positive --specimen csf
```

### 4. Combined Interpretation
```bash
python cli.py combined --bdg 150.0 --gm 1.5
python cli.py combined --bdg 150.0 --crag-positive --mannan 200.0 --anti-mannan 20.0
```

### Parameter Reference
- `bdg`: Interpret Beta-D-Glucan
  - `--value`: BDG value in pg/mL (required)
  - `--false-positives`: Known false positive factors (optional)
- `gm`: Interpret Galactomannan
  - `--index`: GM optical density index (required)
  - `--specimen`: 'serum' or 'bal' (default: serum)
  - `--false-positives`: Known false positive factors (optional)
- `crag`: Interpret Cryptococcal Antigen
  - `--positive`: Flag indicating positive result
  - `--titer`: CrAg titer (e.g., '1:128')
  - `--specimen`: 'serum' or 'csf' (default: serum)
- `combined`: Combined fungal antigen interpretation
  - `--bdg`: BDG value in pg/mL
  - `--gm`: GM index value
  - `--gm-specimen`: GM specimen type (default: serum)
  - `--crag-positive`: CrAg positive flag
  - `--mannan`: Mannan value in pg/mL
  - `--anti-mannan`: Anti-mannan value in AU/mL

---

## 🌐 REST API Server

### Start the server:
```bash
python -m fungal_antigen_triage_agent.cli serve --host 0.0.0.0 --port 8000
```

### API Endpoints:
- `GET /health` - Health check
- `GET /metrics` - Prometheus operational metrics
- `POST /api/audit` - Submit task for multi-agent evaluation
- `POST /api/chat` - Air-gapped supervisory chat
- `GET /api/audit/logs` - Retrieve and verify HMAC audit trail

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

---

## 🐳 Container Deployment

```bash
docker build -t fungal-antigen-triage-agent .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key fungal-antigen-triage-agent
```

Or using Docker Compose:

```bash
docker-compose up -d
```

---

## 📐 Clinical Decision Logic

### Beta-D-Glucan (BDG) Interpretation:
| Value (pg/mL) | Category | Clinical Significance |
|---------------|----------|----------------------|
| < 60 | NEGATIVE | LOW |
| 60-79.9 | INDETERMINATE | MODERATE |
| >= 80 | POSITIVE | HIGH |

### Galactomannan (GM) Interpretation:
| Specimen | Negative | Indeterminate | Positive |
|----------|----------|---------------|----------|
| Serum | < 0.5 | 0.5-0.99 | >= 1.0 |
| BAL | < 0.7 | N/A | >= 0.7 |

### False Positive Factor Awareness:
The system recognizes and adjusts interpretations for known false positive factors including:
- Hemodialysis (HIGH risk for BDG)
- Piperacillin-tazobactam (HIGH risk for GM, MODERATE for BDG)
- IV immunoglobulin (HIGH risk for BDG)
- And many more...

---

## 🛡️ Security Configuration

### Environment Variables:
- `AUDIT_SECRET_KEY`: Secret key for HMAC-SHA256 audit trail (required for production)
- `MODEL_PROVIDER`: LLM provider selection (mock, ollama, claude, openai)

### Security Best Practices:
1. Always set `AUDIT_SECRET_KEY` in production environments
2. The system uses cryptographically random keys as fallback if no key is provided
3. All outbound data is inspected for PHI before logging
4. HMAC-SHA256 chained audit trail ensures tamper evidence

---

## 📁 Project Structure

```
fungal-antigen-triage-agent/
├── agents/                          # Enterprise multi-agent system
│   ├── base.py                      # Security, PHI guard, audit trail
│   ├── models.py                    # Pydantic data models
│   ├── workers.py                   # Specialized worker agents
│   ├── supervisor.py                # Master orchestrator
│   ├── api.py                       # FastAPI REST endpoints
│   ├── metrics.py                   # Prometheus metrics
│   ├── llm_factory.py               # LLM provider factory
│   ├── learning.py                  # Bayesian calibration engine
│   └── streamer.py                  # WebSocket telemetry
├── fungal_antigen_triage_agent/     # Clinical mycology package
│   ├── agents.py                    # Clinical sub-agents
│   ├── engine.py                    # Clinical decision engine
│   ├── models.py                    # Clinical data models
│   ├── cli.py                       # Clinical CLI
│   └── server.py                    # Clinical FastAPI server
├── tests/                           # Test suites
│   ├── test_enrichment.py           # Enrichment module tests
│   └── test_fungal_antigen_triage_agent.py  # Agent system tests
├── myco_sentinel.py                 # Core fungal antigen interpretation
├── cli.py                           # Main CLI entry point
├── simulator.py                     # High-throughput simulation
├── enrichment.py                    # Extended domain features
├── web/index.html                   # Operations console UI
├── Dockerfile                       # Container definition
├── docker-compose.yml               # Multi-container orchestration
└── pyproject.toml                   # Project configuration
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
