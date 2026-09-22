# Temporary BK-KMS Go SDK snapshot

Source: [TencentBlueKing/bk-kms-sdk](https://github.com/TencentBlueKing/bk-kms-sdk),
revision `191a0cdcce7d5201863d18c46bffb4521e38d374` (`go/` subtree).
Includes [PR #56](https://github.com/TencentBlueKing/bk-kms-sdk/pull/56): AES/SM4 CBC
ciphertext length validation returns an error before block decryption.
Runtime source, go.mod, go.sum and the upstream MIT license are copied unchanged.
`MANIFEST.sha256` records the copied files. The same snapshot is used by core-api,
operator and mcp-proxy to keep each component's existing Docker build context self-contained.

The parent module uses a relative `replace` until switching to a published module version.
`v0.0.0` is a local placeholder, not a published SDK version. When switching to a
published module, remove this replacement and snapshot and regenerate dependencies.
Application-specific JSON parsing and credential mapping stay in `pkg/config/kms.go`.
