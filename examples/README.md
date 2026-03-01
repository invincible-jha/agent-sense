# Examples

| # | Example | Description |
|---|---------|-------------|
| 01 | [Quickstart](01_quickstart.py) | Annotate confidence, simplify text, generate suggestions |
| 02 | [Confidence Calibration](02_confidence_calibration.py) | Extract signals, annotate levels, calibrate against ground truth |
| 03 | [Handoff Management](03_handoff_management.py) | Package context, route to human agents, track status |
| 04 | [Accessibility](04_accessibility.py) | WCAG checking, text simplification, screen reader optimisation |
| 05 | [AI Disclosure](05_ai_disclosure.py) | Generate disclosures and transparency reports |
| 06 | [Sense Middleware](06_sense_middleware.py) | Context detection, expertise estimation, middleware pipeline |
| 07 | [LangChain Sense](07_langchain_sense.py) | Wrap LangChain outputs with confidence and handoff detection |

## Running the examples

```bash
pip install agent-sense
python examples/01_quickstart.py
```

For framework integrations:

```bash
pip install langchain   # for example 07
```
