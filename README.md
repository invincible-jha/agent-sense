# agent-sense

Human-agent interaction SDK with accessibility and dialogue management

[![CI](https://github.com/aumos-ai/agent-sense/actions/workflows/ci.yaml/badge.svg)](https://github.com/aumos-ai/agent-sense/actions/workflows/ci.yaml)
[![PyPI version](https://img.shields.io/pypi/v/agent-sense.svg)](https://pypi.org/project/agent-sense/)
[![Python versions](https://img.shields.io/pypi/pyversions/agent-sense.svg)](https://pypi.org/project/agent-sense/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

Part of the [AumOS](https://github.com/aumos-ai) open-source agent infrastructure portfolio.

---

## Features

- User context detection infers expertise level, situation, and channel (web, mobile, voice) from conversation signals, enabling responses calibrated to the user's knowledge and environment
- Confidence annotation and calibration — the `ConfidenceAnnotator` attaches per-claim confidence signals to agent responses and the `Disclaimer` module adds appropriate hedging when confidence falls below configurable thresholds
- Human handoff orchestration: `HandoffRouter` evaluates confidence and topic signals, packages the conversation context, and routes to the appropriate human queue with full conversation history attached
- WCAG 2.1 AA accessibility checker inspects HTML fragments for color contrast, missing image alternatives, heading hierarchy violations, and ambiguous link text
- AI disclosure and transparency utilities that inject required disclosure notices and explain the agent's limitations for regulated interaction contexts
- Suggestion engine ranks follow-up prompts and clarifying questions by relevance to the current conversation turn
- Channel adapters for web, mobile, and voice normalize input and format output appropriately for each surface

## Current Limitations

> **Transparency note**: We list known limitations to help you evaluate fit.

- **Frontend**: Backend Python only — React component library not yet shipped.
- **Languages**: English-only AI disclosure text.
- **Streaming**: No streaming confidence updates.

## Quick Start

Install from PyPI:

```bash
pip install agent-sense
```

Verify the installation:

```bash
agent-sense version
```

Basic usage:

```python
import agent_sense

# See examples/01_quickstart.py for a working example
```

## Documentation

- [Architecture](docs/architecture.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)
- [Examples](examples/README.md)

## Enterprise Upgrade

For production deployments requiring SLA-backed support and advanced
integrations, contact the maintainers or see the commercial extensions documentation.

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md)
before opening a pull request.

## License

Apache 2.0 — see [LICENSE](LICENSE) for full terms.

---

Part of [AumOS](https://github.com/aumos-ai) — open-source agent infrastructure.
