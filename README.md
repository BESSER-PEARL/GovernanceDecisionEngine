# Governance Decision Engine

The Governance Decision Engine runs policies written with [GovernanceDSL](https://github.com/BESSER-PEARL/GovernanceDSL). Its PyPI distribution is `besser-governance-engine`, and its Python import path is `governance`.

## Install

Install it in your project's Python environment:

```bash
pip install besser-governance-engine==1.0.0
```

The package declares Python 3.10 or newer; the release checks were run on Python 3.12.

Check the two primary imports with:

```bash
python -c "import governance.engine.parsing; from governance.engine.semantics.runtime_metamodel import Interaction; print(Interaction)"
```

## Run the engine

The engine module can be started with `python -m governance.engine.decision_engine`; add `-t` for test mode. Running the agent requires a `config.yaml` in the current working directory. A minimal shape is:

```yaml
agent:
  check_transitions:
    delay: 0.1
platforms:
  github:
    personal_token: "YOUR_GITHUB_TOKEN"
    webhook_token: "YOUR_WEBHOOK_SECRET"
    webhook_port: 8901
```

Provide credentials appropriate for your deployment. The package does not bundle a configuration file or a console script. Projects that only import the parsing or runtime modules do not need `config.yaml`.

## Repository layout

- `governance/engine/` contains the engine, parsing helpers, runtime model, and test-mode support.
- `governance/tests/` contains the repository test suites and policy examples. They stay in the repository and are excluded from both release archives.
- `docs/` contains additional documentation under development.

