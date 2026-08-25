# Fungal Antigen Triage Agent

Clinical tool for interpreting invasive fungal disease biomarkers including Beta-D-Glucan, Galactomannan, Cryptococcal Antigen, and Mannan/Anti-mannan with pre-test probability assessment.

## Features

- **Beta-D-Glucan (BDG)**:
  - <60 pg/mL: Negative
  - 60-79 pg/mL: Indeterminate
  - ≥80 pg/mL: Positive (invasive fungal infection)
  - False positive awareness (hemodialysis, IVIG, certain antibiotics, gauze)
- **Galactomannan (GM) Index**:
  - Serum: <0.5 negative, 0.5-0.9 indeterminate, ≥1.0 positive
  - BAL: <0.7 negative, ≥0.7 positive
  - False positive awareness (piperacillin-tazobactam)
- **Cryptococcal Antigen (CrAg)**: Titer-based disease burden estimation
- **Mannan/Anti-mannan**: Combined Candida infection assessment
- **Pre-test Probability**: Host factor-based risk scoring
- **Combined Interpretation**: Multi-marker algorithm

## Quick Start

```bash
# Interpret BDG
python cli.py bdg --value 150.0

# Interpret GM
python cli.py gm --index 1.5 --specimen serum

# Interpret CrAg
python cli.py crag --positive --titer 1:128

# Combined interpretation
python cli.py combined --bdg 150.0 --gm 1.5
```

## Python API

```python
from myco_sentinel import combined_interpretation

result = combined_interpretation(
    bdg_value=150.0,
    gm_index=1.5,
    host_factors={"neutropenic": True, "hematologic_malignancy": True},
)
print(result["combined_severity"])  # "HIGH"
```

## Testing

```bash
python -m pytest test_myco_sentinel.py -v
```

## Standards

- EORTC/MSGERC Consensus Definitions (2019)
- IDSA Guidelines for Aspergillosis (2016)
- IDSA Guidelines for Candidiasis (2016)
- WHO Guidelines for Cryptococcal Disease (2018)

## License

MIT
