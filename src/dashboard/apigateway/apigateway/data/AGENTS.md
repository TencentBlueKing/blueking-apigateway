# Gateway Definitions and API Documentation

Paths here are relative to this directory. `apigw-definitions/` contains gateway
resource registrations; `apidocs/zh/` contains Markdown API documentation.
This checkout has only the `zh` API documentation directory.

Keep affected API views/serializers under `../apis/`, resource YAML, and Markdown
aligned by operationId: HTTP method/path, input/output, status and errors. Preserve
backend ownership, authentication flags and visibility in the registration.

From the inherited Dashboard command root:

```bash
uv run make lint-openapi
uv run make lint-openapi-help
```

The checker supports `SCOPE=v2_open|v2_inner|v2_sync`, `API=<operationId>` and
`JSON=1`; `FIX=1` intentionally creates missing documentation templates, which
still need content review. Dashboard-root `scripts/config.yaml` owns known exceptions and
non-Dashboard backend exclusions. Both lint targets invoke the checker, but its
v2 coverage does not establish correctness of every legacy registration/doc.
For legacy or excluded routes, inspect the owning producer and consumer directly.
