# Governance Decision Engine

This repository contains the implementation of the decision engine for the [GovernanceDSL](https://github.com/BESSER-PEARL/GovernanceDSL).
This repository is structured as follows:
- `docs/` : This folder contains the documentation of the decision engine (Work in Progress)
- `governance/` : This folder contains the engine implementation and tests
  - `engine/` : This folder contains the agent logic, events, and parsing helpers
    - `semantics/` : This folder contains the runtime metamodel implementation and policy enforcement behavior
    - `testing/` : This folder contains the mocks, helpers and additional testing hooks to run the engine in test mode
      - `framework/` : This folder contains the framework to define tests on top of the engine in test mode
  - `tests/` : This folder contains the different tests of the engine
    - `engine/` : This folder contains tests for the different parts of the engine in isolation (WIP)
    - `policies/` : This folder contains tests for the different types of policies (WIP)
    - `kubernetes/` : This folder contains tests replicating kubernetes repository pull requests
    - `policy_examples/` : This folder contains the policy definitions for the tests

## Prerequisite
- Python 3.11
- Recommended: Create a virtual environment
  (e.g. `venv <https://docs.python.org/3/library/venv.html>`_,
  `conda <https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html>`_)
- Clone the [GovernanceDSL](https://github.com/BESSER-PEARL/GovernanceDSL) repository
- Clone this repository
- Install the dependencies (for both repositories) by referencing to the requirements files:

```bash
pip install -r requirements.txt
```

## Run the experiment
Running the experiment is a two steps process:
1. Run the engine in test mode
2. Run the `governance/tests/kubernetes/kubernetes_merge_policy.py`

### Start the engine in test mode
To start the engine in test mode, you first need to add the location of the GovernanceDSL folder on you machine to the `PYTHONPATH` environment variable.
Then, simply run the `governance/engine/decision_engine.py` script with the `-t` option

### Run the PR replication tests
To run the test, simply call pytest on `kubernetes_merge_policy.py`.
```bash
pytest kubernetes_merge_policy.py
```

**NB:** The test ar configured with the path to the `kubernetes.txt` file. By default, you need to start the test while in the `governance/tests/kubernetes` folder. Alternatively, you can edit the tests to change the path at the beginning of the file