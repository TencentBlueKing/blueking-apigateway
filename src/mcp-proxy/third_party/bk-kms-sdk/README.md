# Temporary BK-KMS Go SDK snapshot

Source: user-provided `bk-kms-sdk/go`, revision `58d306a5bf2711d03905e18b3682048149e00bb0`.
Runtime source, go.mod, go.sum and the upstream MIT license are copied unchanged.
`MANIFEST.sha256` records the copied files. The same snapshot is used by core-api,
operator and mcp-proxy to keep each component's existing Docker build context self-contained.

The parent module uses a relative `replace` until the SDK is publicly available.
`v0.0.0` is a local placeholder, not a published SDK version. When switching to a
published module, remove this replacement and snapshot and regenerate dependencies.
Application-specific JSON parsing and credential mapping stay in `pkg/config/kms.go`.
