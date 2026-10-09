# Legacy ESB

This subtree is outside normal API Gateway development scope. Inspect or change
it only when the task explicitly includes legacy ESB or a verified dependency
requires it. Do not infer that its consumers or CI have been removed:
`.github/workflows/esb.yaml` still defines component checks. For an authorized
code change, inspect this subtree's Makefile and requirements before selecting
its runtime and checks; Dashboard's current Python environment is not its contract.
