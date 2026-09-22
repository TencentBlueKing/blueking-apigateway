# 临时本地 KMS SDK

`bk_kms_sdk-1.0.0-py3-none-any.whl` 从用户提供的 `bk-kms-sdk/python` 构建。

- 源码 revision：`58d306a5bf2711d03905e18b3682048149e00bb0`（构建前工作区干净）。
- 包版本：`1.0.0`，Python `>=3.11,<3.15`。
- 依赖：`bk-crypto-python-sdk==4.1.1`，与 Dashboard 已有依赖一致。
- SHA-256：`6e88e3e941154253a6f5490f8de42ed1642fa3d860ec9b4d8d7d511cb7a9d596`。
- 构建命令：在 SDK 的 `python/` 目录执行 `make build PYTHON=.venv/bin/python`。
- 许可证：MIT，包含在 wheel 的 `dist-info/licenses/LICENSE` 中。

wheel 只包含 SDK 代码、类型标记及包元数据，不包含测试私钥或凭证。
`pyproject.toml` 的相对路径 source 供本地和镜像构建共同使用；无需访问未公开的源码仓库。
更新包后同步校验和、锁文件及本说明。正式发布到包索引后，再切换依赖来源。
