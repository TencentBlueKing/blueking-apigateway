# Dashboard 单元测试

以下命令均在 `src/dashboard` 执行。首次准备环境：

```bash
uv sync --locked --all-extras --dev
uv run make edition-ee
```

需要验证其他 edition 时，先激活对应 overlay。单独设置 `EDITION` 不会切换源文件。
Makefile 测试入口会加载 `apigateway/apigateway/conf/unittest_env` 并指定 Django settings，
不需要复制环境变量或手动进入 Django 项目目录。

## 选择测试范围

| 场景 | 命令 | 覆盖范围 |
| --- | --- | --- |
| 局部修改、回归开发 | `uv run make test-fast TEST_WORKERS=0 TEST_PATHS=apigateway/tests/path/to/test_file.py` | 指定路径的普通测试，不执行迁移 |
| 普通测试全集快跑 | `uv run make test-fast` | 全部未标记 `migration` 的测试，不执行迁移 |
| 迁移专项 | `uv run make test-migrations` | 标记 `migration` 的测试，启用迁移 |
| 广泛/共享改动、CI 完整门禁 | `uv run make test` | 包含迁移测试的完整集合，启用迁移 |
| 上轮失败项复查 | `uv run make test-lf` | pytest 缓存记录的失败项；没有记录时按 pytest 默认行为执行全部 |
| 覆盖率 | `uv run make test-cov` | 启用迁移并统计覆盖率 |
| 单进程调试 | `uv run make test-pdb TEST_PATHS=apigateway/tests/path/to/test_file.py` | 指定路径，失败时进入调试器 |

局部修改先运行受影响测试，再按调用关系扩展范围。Python 代码修改还需
`uv run make lint-check`。修改共享 fixture、测试配置、跨模块行为时运行完整门禁。
`test-fast` 和 `test-lf` 均不能代替完整门禁；迁移改动还需检查受影响的普通行为。
已有检查通过后，只有相关代码、输入、运行环境、命令或范围改变才需要重跑。

## 并发与筛选

并行入口使用 pytest-xdist 的 `worksteal`，避免耗时较长的模块被整组分给一个 worker。
默认 `TEST_WORKERS=auto`，按可用物理核数选择，最多 8 个 worker，兼顾共享机器与小规格 CI。
显式设置数字可覆盖默认上限；`0` 表示不启用并行，适合少量测试。

```bash
uv run make test TEST_WORKERS=16
uv run make test-fast TEST_WORKERS=0 TEST_PATHS=apigateway/tests/utils/test_sensitive_cleaner.py
uv run make test-fast TEST_WORKERS=0 TEST_PATHS='apigateway/tests/path/to/test_file.py::TestClass::test_method'
uv run make test-fast TEST_PATHS='apigateway/tests/biz/resource apigateway/tests/apis/web/resource'
PYTEST_ADDOPTS='--durations=20 --tb=short' uv run make test
```

`TEST_PATHS` 相对 `src/dashboard/apigateway`，支持多个路径及 pytest nodeid。
`test` 默认执行全集；设置 `TEST_PATHS` 或其他筛选条件后只能报告为指定范围验证。
迁移测试在 `test-fast` 中会被排除，即使 `TEST_PATHS` 指定了该文件；请使用 `test-migrations`。

## 迁移测试与数据库

新增验证 schema/data migration 的测试必须加 `pytest.mark.migration`。
迁移专项文件可使用模块级标记，并保留事务测试原有的数据库隔离方式：

```python
pytestmark = [pytest.mark.migration, pytest.mark.django_db(transaction=True)]
```

完整门禁和迁移专项入口显式启用 `--migrations`。快跑入口使用 `--nomigrations`，
从当前模型创建测试表，因此不能证明历史迁移、数据回填或升级路径正确。
CI 继续运行 `make test`，覆盖普通测试与迁移测试。

默认测试数据库是各 worker 独立的内存 SQLite。`--reuse-db` 不会让内存库在下一次
命令中继续存在；每次运行仍会初始化数据库。若以后配置持久测试库，模型或迁移变化后
需要重建数据库，并保证不同工作树、edition 和 worker 不共享可变测试数据。
