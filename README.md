This repository contains our team’s BrowserGym Green Agent for evaluating web-based tasks on the **AgentBeats** platform. It supports three official BrowserGym benchmarks:**AssistantBench**, **MiniWoB**, and **WebLINX**.

All benchmarks are integrated into a single Green Agent that can:

- Initialize and manage BrowserGym environments

- Evaluate task requests from AgentBeats

- Validate white-agent actions against task requirements

- Return success/failure results and final scores

This unified evaluator provides a consistent assessment pipeline across all three benchmarks and supports both local demonstration and remote deployment on AgentBeats. It is submitted as our team’s entry for the AgentBeats Green Agent Challenge.

## Adapter regression tests

From the repository root, run:

```shell
python -B -m unittest discover -s tests -p "test_*.py" -v
```

The root `tests/` suite uses only the Python standard library. It loads the
actual tool modules while replacing optional SDK imports with test stubs, so no
GPU, model download, browser, credentials, or third-party packages are needed.
GitHub Actions runs this suite on Windows and Linux with Python 3.12 and 3.14.

The tests check that MiniWoB forwards the submitted action unchanged, permits
exactly the configured number of actions, and reports worker errors. They also
check WebLINX's reference-action lookup against synthetic cases and a bundled
validation row, including zero and partial credit and summary statistics.

These are adapter tests, not end-to-end AgentBeats or BrowserGym runs. They do
not validate SDK decorators, browser execution, or model performance. The older
tests under `scenario4assistantbench/tests/` are a separate integration suite
with external dependencies and are not included in this command.

See [evaluation notes](docs/evaluation-notes.md) for the reproduced defects and
remaining limitations before reporting benchmark scores.
