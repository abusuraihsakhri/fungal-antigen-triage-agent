# Fungal Antigen Triage Agent

A research and educational Python utility for interpreting selected fungal antigen and biomarker results. It includes a browser application, command-line interpreter, and two separate experimental API/agent implementations.

**Status:** Unvalidated demonstration software. **Not for diagnosis, prescribing, or patient care.** The rule thresholds, host-factor scores, and interpretive statements in this repository have not been clinically validated. Applicability depends on the laboratory assay, specimen, population, and local diagnostic protocol.

## Browser application

The GitHub Pages build provides a responsive form for beta-D-glucan (BDG), galactomannan (serum/BAL), cryptococcal antigen (CrAg), and mannan/anti-mannan results, including combined interpretations and downloadable JSON. No backend is required.

The browser runs the actual [Python interpretation module](myco_sentinel.py) using **Pyodide 0.27.7**. The interpreter and its WebAssembly assets load from a pinned external CDN on first use, so an initial network connection is required. To run locally:

~~~bash
python -m http.server 8008
# Open http://127.0.0.1:8008/web/
~~~

The UI accepts assay measurements rather than patient names or identifiers. Case information is processed in browser memory and is not sent to an application server. The browser makes requests for static code and the Pyodide runtime; those requests expose ordinary connection metadata to hosting providers. No analytics or case-storage service is included.

## CLI interpretation

Python 3.10 or newer is supported.

~~~bash
python -m pip install -e ".[server,test]"
fungal-antigen-triage bdg --value 150
fungal-antigen-triage gm --index 1.5 --specimen serum
fungal-antigen-triage crag --positive --titer 1:128 --specimen csf
fungal-antigen-triage combined --bdg 150 --gm 1.5
python cli.py bdg --value 150 --false-positives hemodialysis
~~~

The interpreter supports BDG, galactomannan, CrAg, mannan/anti-mannan, an illustrative host-factor risk score, and combined summaries. Known analytical confounders can be supplied to individual BDG and GM functions via the CLI. Invalid numerical measurements are reported as errors rather than silently classified.

The host-factor score is a heuristic point sum, **not a validated pre-test probability model**. Single or combined positive results do not establish invasive fungal disease; negative results do not exclude it.

## Experimental APIs

Two independent FastAPI surfaces are present and should not be confused:

| App | Startup command | Main functionality |
| --- | --- | --- |
| Generic audit API | uvicorn agents.api:app --host 127.0.0.1 --port 8000 | /health, /metrics, /api/audit, /api/chat, /api/audit/logs |
| Illustrative clinical API | python -m fungal_antigen_triage_agent.cli serve | /health, /api/audit, /api/chat |

The generic audit API evaluates arbitrary primary and secondary metrics with illustrative thresholds; it does **not** implement the specific BDG/GM/CrAg assay interpretations exposed by myco_sentinel.py. Its /metrics endpoint returns JSON, not Prometheus text. The chat provider factory currently returns deterministic placeholder responses, not clinical-model inference.

**Security:** Both APIs lack user authentication and authorization; they must not be published directly to the internet or supplied with identifiable patient data. The generic audit API includes regex-based identifier screening and an in-memory chained HMAC-SHA256 event log. Regex screening is incomplete and **does not establish HIPAA de-identification**. Audit records are not persistent across restarts.

## Docker

The Docker image starts the **generic audit API** and includes a /health check. Compose binds port 8000 to loopback by default.

~~~bash
cp .env.example .env
# Set AUDIT_SECRET_KEY to a newly generated, unique secret in .env.
docker compose up --build
# Open http://127.0.0.1:8000/health
~~~

Do not use the removed repository example signing key. Rotate keys if one has ever been used in deployment. Store secrets outside source control; never place them in browser assets or GitHub Pages files.

## Tests and deployment

~~~bash
python -m pip install -e ".[server,test]"
python -m pytest -q
python -m compileall -q agents fungal_antigen_triage_agent myco_sentinel.py
node --check web/app.js
~~~

GitHub Actions runs Python tests across 3.10–3.12, API smoke tests, static route checks, and an end-to-end Chromium/Pyodide test. Successful pushes to master trigger a GitHub Pages artifact build containing only the HTML, JavaScript, and interpretation Python source. The Pages publishing source must be configured for GitHub Actions in repository settings.

## Source layout

- **myco_sentinel.py:** fungal antigen interpretation functions and their CLI.
- **web/:** Pyodide browser frontend and Chromium smoke test.
- **fungal_antigen_triage_agent/:** experimental clinical coordinator, CSV CLI, and API.
- **agents/:** experimental metric worker agents, audit log, and generic API.
- **enrichment.py:** optional independent heuristic modules.
- **tests/** and **test_myco_sentinel.py:** regression and domain-function test suites.
- **Dockerfile**, **docker-compose.yml:** containerized generic audit API.

## License

[MIT](LICENSE).
