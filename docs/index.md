# agent-sense

Human-Agent Interaction SDK — dialogue management, confidence indicators, transparency, and accessibility for AI agents.

[![CI](https://github.com/invincible-jha/agent-sense/actions/workflows/ci.yaml/badge.svg)](https://github.com/invincible-jha/agent-sense/actions/workflows/ci.yaml)
[![PyPI version](https://img.shields.io/pypi/v/agent-sense.svg)](https://pypi.org/project/agent-sense/)
[![Python versions](https://img.shields.io/pypi/pyversions/agent-sense.svg)](https://pypi.org/project/agent-sense/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

---

## Installation

```bash
pip install agent-sense
```

Verify the installation:

```bash
agent-sense version
```

---

## Quick Start

```python
import agent_sense

# See examples/01_quickstart.py for a working example
```

---

## Key Features

- **User context detection** infers expertise level, situation, and channel (web, mobile, voice) from conversation signals, enabling responses calibrated to the user's knowledge and environment
- **Confidence annotation and calibration** — the `ConfidenceAnnotator` attaches per-claim confidence signals to agent responses and the `Disclaimer` module adds appropriate hedging when confidence falls below configurable thresholds
- **Human handoff orchestration** — `HandoffRouter` evaluates confidence and topic signals, packages the conversation context, and routes to the appropriate human queue with full conversation history attached
- **WCAG 2.1 AA accessibility checker** inspects HTML fragments for color contrast, missing image alternatives, heading hierarchy violations, and ambiguous link text
- **AI disclosure and transparency utilities** that inject required disclosure notices and explain the agent's limitations for regulated interaction contexts
- **Suggestion engine** ranks follow-up prompts and clarifying questions by relevance to the current conversation turn
- **Channel adapters for web, mobile, and voice** normalize input and format output appropriately for each surface

---

## Links

- [GitHub Repository](https://github.com/invincible-jha/agent-sense)
- [PyPI Package](https://pypi.org/project/agent-sense/)
- [Architecture](architecture.md)
- [Changelog](https://github.com/invincible-jha/agent-sense/blob/main/CHANGELOG.md)
- [Contributing](https://github.com/invincible-jha/agent-sense/blob/main/CONTRIBUTING.md)

---

> Part of the [AumOS](https://github.com/aumos-ai) open-source agent infrastructure portfolio.
