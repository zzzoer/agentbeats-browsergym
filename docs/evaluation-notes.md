# Evaluator regression notes

## MiniWoB action fidelity and budget

The adapter previously replaced every submitted action with a hardcoded Submit
button click. For example, a request to check a checkbox dispatched a Submit
click to the worker instead. The adapter now forwards the submitted action.

The budget guard previously used `count > limit`, which permitted an eleventh
dispatch when the configured limit was ten. It now rejects calls when
`count >= limit`, before dispatching or consuming a worker result.

The five MiniWoB tests exercise these boundaries, state/reward updates, and
worker failures. Against the previous implementation, three tests fail; after
the fix, all five pass. Worker results are provided by in-memory queues.

## WebLINX reference action

Dataset rows store the reference action under `action`. The scorer previously
looked up `expected_action`, which is an output field of `get_weblinx_task`, not
a field in the stored row. Consequently, even an exact reference prediction
was compared with an empty action and rejected.

The scorer now reads `action` directly. Seven tests cover matching and
mismatching predictions, existing partial credit, missing reference data,
statistics, and the first bundled validation row. Six fail against the old
implementation; all seven pass after this correction. This change preserves
the existing custom scoring rules.

## Reproduce

Run from the repository root with Python 3.12 or newer:

```shell
python -B -m unittest discover -s tests -p "test_*.py" -v
```

The assertions run the real adapter functions. Optional imports and the
AgentBeats tool decorator are stubbed; no benchmark model has been run as part
of this validation. Passing these tests does not establish benchmark accuracy.

## Remaining limitations

- `get_weblinx_task` still exposes the reference action in its returned
  `expected_action` field. If that payload is sent to the evaluated agent,
  it leaks the answer. Remove the reference from agent-visible observations
  and test that boundary before collecting model benchmark scores.
- WebLINX scoring is project-specific. Equality to this scorer is not evidence
  of equivalence to the official WebLINX evaluation protocol. Malformed or
  missing action arguments need a separate validation policy.
- The MiniWoB tests do not start the worker or a browser. Uninitialized calls,
  late results after timeouts, environment lifecycle and episode termination
  need separate integration coverage.
- AssistantBench state management and its existing integration tests are
  outside these two fixes.

This is a team project. Attribute the original implementation and subsequent
fixes separately when describing individual contributions.
