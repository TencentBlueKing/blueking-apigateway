# Dashboard：ty + django-types 报错调研

2026-11-02 在源码基线 `7125dd8e43a193053512153c61a512b4ad4fd6c1`、EE edition 下运行。
`ty 0.0.95 + django-types 0.24.0` 存根实际生效后，全量 dashboard 有 **1,014 条诊断：987 条错误、27 条警告，涉及 246 个文件**。
排除 editions、migrations、conf 后，有 **962 条诊断：936 条错误、26 条警告，涉及 224 个文件**。
建议先与 mypy 并行调研，逐项修复和限定豁免范围，暂时不能直接替换现有门禁。

本次交付统计、完整定位清单和处理建议。下文的修复方案是后续建议；业务代码、依赖声明、锁文件和 CI 门禁没有改动。

## 环境与统计口径

| 项目 | 本次值 |
| --- | --- |
| Python | 3.14.6，项目要求 `>=3.14,<3.15` |
| Django / DRF | 5.2.17 / 3.18.1，来自现有锁文件 |
| ty / django-types | 0.0.95 / 0.24.0，独立环境安装 |
| edition | `uv run make edition-ee` |
| 工作目录 | `src/dashboard` |
| 模块搜索目录 | 显式加入 `apigateway` |
| 默认规则和 ignore | 保留 ty 默认规则及默认的 `type: ignore` 处理 |

[完整清单](ty-django-types-diagnostics.tsv)包含全量的 1,014 条诊断，按文件、行、列排序；路径相对于 `src/dashboard`。
`in_aligned_scope` 表示是否属于上述排除后的范围，`suppressed_in_experiment` 表示是否被下文的局部豁免实验移除。
清单保留每条诊断的规则和类型描述，将消息里的双引号字符串字面量统一替换为 `<string literal>`，避免复制测试输入或配置值。

ty 的 `--output-format gitlab` 输出是 JSON 数组；本次其中 `major` 对应 error，`minor` 对应 warning。
按数组中的诊断条目计数，不按代码行数、消息行数或根因数计数。一处联合类型和一条根因可能产生多条诊断。

当前项目没有 ty 配置或 django-types 依赖。现有 [Makefile](../Makefile) 的 lint-check 仍调用 mypy。
以下“近似 mypy 范围”只对齐现有 [mypy 排除目录](../pyproject.toml)，没有模拟 `follow_imports="skip"`、
`ignore_missing_imports=true`，也没有让 ty 跳过未注解函数体。因此两者通过与否不能作为同等严格度的比较。
EE 激活后的可见文件及存根均按实际工作树检查；全量命令也包含 editions 原始目录，可能与激活入口重复报错。
排除 editions 后仍保留激活的 EE 入口，不把未激活的其他 edition 结果混入业务清单。

## 复现命令

在 `src/dashboard` 执行；使用专属的 `.venv-ty`，避免向日常 mypy 环境安装 Django 存根。

```bash
uv sync --locked --all-extras --dev
uv run python --version
uv run make edition-ee

UV_PROJECT_ENVIRONMENT=.venv-ty uv sync --locked --all-extras --dev
uv pip install --python .venv-ty/bin/python ty==0.0.95 django-types==0.24.0

# 全量统计；有诊断时 ty 返回 1，不代表采集失败。
UV_PROJECT_ENVIRONMENT=.venv-ty uv run --no-sync ty check \
  --python .venv-ty/bin/python --extra-search-path apigateway \
  --exclude .venv-ty/ --output-format gitlab --no-progress --color never . \
  > ty-full.json

# 近似现有 mypy 的目录范围，仍保留 tests。
UV_PROJECT_ENVIRONMENT=.venv-ty uv run --no-sync ty check \
  --python .venv-ty/bin/python --extra-search-path apigateway \
  --exclude .venv-ty/ --exclude '**/editions/**' \
  --exclude '**/migrations/**' --exclude '**/conf/**' \
  --output-format gitlab --no-progress --color never . > ty-aligned.json

uv run --locked mypy --config-file=pyproject.toml .
```

本次实际使用仓库外的专属虚拟环境；上面换成相对目录并显式排除它，避免将环境文件计入统计。
`--no-sync` 必须保留，否则 uv 会按未添加 ty 的原锁文件同步环境。
若要逐条看完整解释，将 `--output-format gitlab` 改为 `full`，也可只传清单中的文件。

遇到过的采集陷阱：直接运行 `uv run --with ty --with django-types`，在本次环境下 Python 能找到 django-types，
但 ty 没有读取 uv 临时环境通过 `.pth` 加载的存根目录，仍把 `Foo().name` 判为 `CharField`、把 `Foo.objects` 判为不存在。
这组结果与未启用存根完全一致，不能作为“ty + django-types”结果。
显式指定包含实际 site-packages 的环境后，最小模型的 `name` 被判为 `str`、`objects` 被判为 `BaseManager[Foo]`。
正式统计使用完整独立环境；另验证了非法参数调用仍触发 `invalid-argument-type`。这只是本次环境的复现现象，不推断所有 uv 安装都有该问题。

## 总量与范围

| 实验 | 诊断 | 说明 |
| --- | ---: | --- |
| ty，不启用 Django 存根 | 2,413 | 其中 2,386 error、27 warning；大量字段被误判为 Field 对象 |
| ty + django-types，全量 | 1,014 | 比上一组减少 1,399 条，约 58.0%；并非剩余每条都是真实缺陷 |
| 同上，排除 editions/migrations/conf | 962 | 比全量少 52 条；已验证与全量清单按这三类路径过滤完全一致 |
| 上述范围，再做局部豁免实验 | 904 | 精确移除 37 条 Meta 覆盖及 21 条未使用 ignore 提示，仍有 899 error、5 warning |
| 现有 mypy 命令 | 0 error | 检查 1,596 个文件，通过；输出提示未注解函数体默认不检查 |

全量按以下互斥顺序划分：editions → migrations → conf → tests → 其余生产代码/工具。

| 范围 | 诊断 |
| --- | ---: |
| 其余生产代码/工具 | 485 |
| tests（排除 editions 内测试） | 477 |
| editions 原始目录（含其中测试） | 23 |
| conf（含测试配置目录） | 19 |
| migrations | 10 |
| 合计 | 1,014 |

## 所有诊断规则

| 规则 | 全量 | 近似 mypy 范围 |
| --- | ---: | ---: |
| `unresolved-attribute` | 428 | 422 |
| `invalid-argument-type` | 275 | 257 |
| `invalid-assignment` | 70 | 62 |
| `invalid-method-override` | 50 | 50 |
| `invalid-attribute-override` | 37 | 37 |
| `not-subscriptable` | 31 | 31 |
| `unused-type-ignore-comment` | 21 | 21 |
| `no-matching-overload` | 20 | 5 |
| `unsupported-operator` | 20 | 20 |
| `call-non-callable` | 13 | 13 |
| `unresolved-import` | 12 | 8 |
| `not-iterable` | 8 | 8 |
| `missing-argument` | 7 | 7 |
| `invalid-type-form` | 3 | 3 |
| `invalid-yield` | 3 | 3 |
| `invalid-return-type` | 3 | 3 |
| `invalid-mutable-override` | 3 | 3 |
| `redundant-cast` | 2 | 2 |
| `too-many-positional-arguments` | 2 | 2 |
| `deprecated` | 1 | 1 |
| `possibly-missing-submodule` | 1 | 1 |
| `redundant-condition` | 1 | 1 |
| `invalid-parameter-default` | 1 | 1 |
| `pydantic-discarded-extra-argument` | 1 | 0 |
| `unknown-argument` | 1 | 1 |

## 可以修复的主要类别

### 属性缺失：先区分动态属性、可空值和过宽的返回类型

`unresolved-attribute` 全量 428 条，不能整体忽略。
其中 124 条描述明确包含对 `None` 的属性访问；35 条 `id` 错误里只有 6 条是基类 `Model` 未声明 id，其余多数涉及可空值或联合类型。
普通模型的 `objects` 和字段描述符在存根生效后已经被正确识别，剩余 2 条 `objects` 诊断来自测试参数的联合类型。

- 请求扩展：87 条属性名是 `gateway`，其中 83 条来自 `HttpRequest` 的自定义 gateway 属性。
  [权限校验](../apigateway/apigateway/apis/permissions.py)和其他 API permissions 会动态写入它。
  可在真正保证权限链已写入属性的入口使用项目专用 Request 类型，并为 gateway/app/tenant 等扩展补注解；不能让所有 HttpRequest 都无条件具备 gateway。
  `query_params`、Mixin 中的 request/kwargs/get_queryset 等也应补足所属 DRF 层的契约。
- 转换器测试：37 条 `upstream` 都在 `GatewayApisixModel` 上，31 条 `plugins` 中有 22 条同样来自该基类。
  转换器返回类型过宽；在消费前收窄到 Service/Route，或完善具体返回类型，避免向基础模型添加不存在的字段。
- ORM 动态字段与关系：django-types 不自动生成所有反向关系、隐式 id 或字符串 ForeignKey 目标。
  在 TYPE_CHECKING 内补真实字段和关系类型，或使用已经存在的明确 pk；保留数据库和运行时字段定义。
  自定义 I18nProperty/JSONField 还需要检查其描述符注解。不要为了检查器改变生产字段或数据库结构。
- 可空属性：对 `.first()`、`.get()`、可空关系的结果查明实际契约；处理缺失值，或在已有必然存在的条件下做类型收窄。
  对没有来源证明的 None 访问，不能用 cast 或 ignore 代替边界处理。

### 参数、赋值和可空值

`invalid-argument-type` 275 条、`invalid-assignment` 70 条。
275 条参数诊断中 158 条描述含有 None；其中也有容器不变性问题，不能直接当作 158 个可空缺陷。

- [资源文档导入](../apigateway/apigateway/apis/open/resource_doc/views.py)将 `list[ArchiveDoc]` / `list[OpenAPIDoc]` 传给 `list[BaseDoc]`。
  Python 的 list 是不变容器；若接收者只读，考虑 Sequence/Iterable；若会写入，保持 list 契约并显式构造合适的列表。
- MigrationExecutor 测试中有 23 条 `list[tuple[str, str]]` 到 `list[tuple[str, str | None]]` 的不变性报错，可给 targets 精确注解。
- [权限操作审计](../apigateway/apigateway/apis/web/permission/views.py)有 5 条把拼接字符串作为 `instance_id: int` 传入的诊断。
  核对审计存储和批量操作的真实契约，再修正边界注解或调用；不能凭类型检查擅自改变审计数据格式。
- `loads(str | None)`、可空 URL port、可空时间比较或相减，需要核对默认值和业务保证。
  [网关逻辑](../apigateway/apigateway/biz/gateway/gateway.py)和[同步任务](../apigateway/apigateway/controller/tasks/syncing.py)是具体定位入口。
- `not-subscriptable` 31 条、`not-iterable` 8 条、`unsupported-operator` 20 条大多需要同样的边界分析或联合类型收窄。
  [renderer](../apigateway/apigateway/common/renderers.py)的可选 renderer_context 默认值和
  [模板错误](../apigateway/apigateway/biz/resource_doc/exceptions.py)的可选 filename 都应结合调用链判断。

### 覆盖签名和容器不变性

`invalid-method-override` 50 条，包含以下已核对的原因。

- 36 条 Serializer.validate：子类参数叫 data/value，DRF 基类参数叫 attrs，允许关键字调用时不兼容。
  统一参数名及内部引用可以修复；DRF 正常路径按位置调用不能证明公开方法的关键字兼容。
- 2 条 Serializer.to_representation 也应对齐基类参数契约。
- 5 条 convert：子类返回 `list[GatewayApisixModel]` 等，基类声明 `list[ApisixModel]`。
  [基类](../apigateway/apigateway/controller/convertor/base.py)与各具体转换器须选择一致契约；若只读可考虑协变 Sequence，若保留 list 则显式对齐类型。
- JWT middleware 的 get_user 参数序列与 apigw-manager 不一致，基类多了 gateway_name/tenant_id；核对实际调用后修正。
- 其余为 notice.send、OpenAPI validator 和测试替身的 distribute/revoke 签名，按真实接口修复。

这些原因不是统一的 Django 插件缺失，不能整体关闭 `invalid-method-override`。

### 少量明确的注解问题

- `invalid-type-form` 3 条：[个人工作台 views](../apigateway/apigateway/apis/web/personal_workbench/views.py)的
  `filter_backends: list[type]` 与类内 `def list` 冲突。可显式使用 builtins.list 或已导入的 typing.List；不必改业务方法名。
- `invalid-parameter-default` 1 条：[EtcdRegistry](../apigateway/apigateway/controller/registry/etcd.py)的
  `etcd_client: Etcd3Client = None` 应声明可选类型，内部已有备用 client 逻辑。
- `invalid-return-type` 3 条中，[apply_permission](../apigateway/apigateway/biz/permission/manager.py)声明
  `AppPermissionRecord`，实际返回 create_apply_record 创建的 `AppPermissionApply`。
  OpenAPI schema 的 Mapping key 类型和模板错误的可选返回值另行对齐。
- `invalid-yield` 3 条：[OpenAPI validator](../apigateway/apigateway/biz/openapi/schema.py)使用 prance.ValidationError 注解，
  实际 yield 的是 jsonschema ValidationError 及其子类；修正异常类型注解。
- `invalid-mutable-override` 3 条来自测试继承模型，子类缩小可写字段类型；给测试对象一致的字段类型或调整构造方式。

### 测试里的预期非法调用和推断问题

- `missing-argument` 7 条均在转换器/transformer 测试；包含 `pytest.raises(TypeError)` 下故意省略 apisix_version 的调用。
  给预期失败的调用加精确 `# ty: ignore[missing-argument]`，保留失败断言；不能全局忽略或给生产构造器添加默认值。
- `call-non-callable` 13 条中，ESB 参数表把 model、params、will_error 混在无注解 dict 中，导致 model 被推断为包含 bool/dict 的联合类型。
  用 TypedDict 或测试参数类型表达行结构。另有 RequestIDMiddleware.get_response 的 None 推断，需要按 middleware 构造契约处理。
- `too-many-positional-arguments` 2 条来自迁移测试保存 class.add_field 后显式传 schema_editor。
  本次核对运行时签名 `(self, model, field)`，但类型分析把该取值视为 bound method；核对描述符及 Callable 注解后再局部豁免。
- 其余混合参数表、Pydantic 基类返回值和 `.first()` 结果，需要表达真实对象类型；不建议排除整个 tests。

## 可以局部忽略或修正存根的类别

| 类别 | 建议 | 本次证据与边界 |
| --- | --- | --- |
| 37 条 `invalid-attribute-override` | 针对 Meta 定义行豁免，或对命中的 13 个文件设置临时 override | 37 条全部为内部类 Meta 覆盖；Django/DRF 按约定读取它。文件 override 会抑制该文件未来其他属性覆盖错误，逐行规则豁免更窄 |
| 21 条 `unused-type-ignore-comment` | 与 mypy 并行期间可暂时关闭这个提示 | 不能直接删 mypy 所需的 ignore；后续使用 ty 的精确规则与 mypy 注释分别管理 |
| 12 条 `unresolved-import` | 按缺失原因分组，不能整体忽略 | 8 条是可选模块/本地配置/editions 原始目录的相对导入，4 条是已安装 Django 运行时成员未写入存根 |
| 存根遗漏 | 补存根或对已验证存在的成员逐行豁免 | `MAX_URL_LENGTH`、`smart_bytes` 在本次 Django 运行时存在；django-types 的对应 pyi 未声明它们 |
| 5 条 charset 赋值 | 优先补存根 setter，或逐行豁免 | HttpResponse 运行时 property 有 setter；本次存根只声明 getter，DownloadableResponse 继承该属性 |
| 动态 monkeypatch 的 1 条 `unknown-argument` | 验证补丁后逐行豁免或给替换函数/调用边界补类型 | [etcd 补丁](../apigateway/apigateway/utils/etcd_monkeypatch.py)已替换 MultiEndpointEtcd3Client.__init__ 并接受 uses_secure_channel，ty 仍按原签名分析 |
| editions/migrations/conf | 可沿用当前 mypy 范围策略，但单独保留清单 | 本次少 52 条，只表示没有在主门禁诊断这些文件，不证明它们无问题 |
| 其余警告 | 保持 warning，按原因处理 | redundant-cast、deprecated、possibly-missing-submodule、redundant-condition、Pydantic extra argument 等不能都当噪声；重复 cast 不影响功能，Pydantic 丢弃字段需核对测试意图 |

8 条可选/相对导入包括 utils_ext、tencent_pypi、两个 SDK generator、SDK manager 的 python_legacy、
settings_dev.local_settings，以及 editions 原始 SDK manager 的 base/mixins。
4 条存根成员缺失为 MAX_URL_LENGTH 1 条、smart_bytes 3 条。
近似 mypy 范围下剩 8 条导入诊断，其中可选模块 5 条、运行时成员缺失 3 条。

### 局部豁免实验

本次用命令行 TOML 配置，仅关闭 unused-type-ignore-comment，并在完整清单命中的 13 个文件中关闭 invalid-attribute-override。
实际运行结果精确少了 58 条：962 → 904，未改变其他规则。下面示例只展示其中一个文件；全量实验覆盖的文件可从清单中筛选。

```toml
# 以下是 pyproject.toml 的候选配置示例，本次没有写入项目配置。
[tool.ty.rules]
unused-type-ignore-comment = "ignore"

[[tool.ty.overrides]]
include = ["apigateway/apigateway/apis/open/permission/serializers.py"]

[tool.ty.overrides.rules]
invalid-attribute-override = "ignore"
```

不建议关闭 unresolved-attribute、invalid-argument-type、invalid-assignment、invalid-method-override 或 unresolved-import 整类。
这些规则同时覆盖真实的边界问题、接口契约、类型注解问题和少量存根噪声。即便采用上述范围和局部豁免，也远未清零。

## 报错最多的文件

路径相对于 `src/dashboard`。同一根因可能在一个文件中多次出现，数量只用于排序。

| 文件 | 全量诊断 |
| --- | ---: |
| `apigateway/apigateway/tests/controller/convertor/test_service.py` | 53 |
| `apigateway/apigateway/apis/web/mcp_server/views.py` | 36 |
| `apigateway/apigateway/tests/controller/convertor/test_service_health_check.py` | 34 |
| `apigateway/apigateway/apis/web/plugin/views.py` | 21 |
| `apigateway/apigateway/tests/controller/convertor/test_route.py` | 20 |
| `apigateway/apigateway/apis/web/permission/views.py` | 18 |
| `apigateway/apigateway/tests/apis/web/permission/test_views.py` | 18 |
| `apigateway/apigateway/service/prometheus/dimension.py` | 17 |
| `apigateway/apigateway/apis/web/personal_workbench/views.py` | 16 |
| `apigateway/apigateway/tests/components/test_bkiam.py` | 16 |

## 后续建议与验证边界

先固定检查器和存根版本，在 CI 中并行报告；保持现有 mypy 门禁。处理顺序建议为：

1. 确认运行时环境和存根解析，保存可复现范围及完整清单。
2. 修复明确的注解和签名问题；对请求扩展、ORM 动态属性及返回模型集中补类型。
3. 为测试参数表加类型，收窄具体 APISIX 模型，保留预期非法调用的精确豁免。
4. 对可空值逐项核对调用链和业务保证，用有意义的测试验证行为修复；不批量 cast 或 assert。
5. 对存根遗漏、Meta 和 edition 可选模块记录局部豁免理由，定期随版本检查。
6. 稳定收敛后，再决定是否移除 mypy。不能以全局禁用主要规则所得的“通过”作为替换依据。

本次已经执行全量、近似 mypy 范围、无存根对照、局部豁免及最小模型正反例验证；
检查了对应运行时 Django API、存根内容和代表性生产/测试调用。现有 mypy 检查通过。
类型检查采集时 ty 返回 1；采集和校验程序仅在该退出码符合预期、JSON 结构正确、计数和范围一致时通过，未使用 --exit-zero 掩盖诊断。
没有声称业务代码修复完成，也没有运行应用单元测试、完整 lint-check 或集成验证；本次只改调研文档与诊断数据，按仓库 Markdown-only 规则验证引用、数据和差异。

参考：[django-types 上游使用说明](https://github.com/sbdchd/django-types/blob/main/README.md)、
[ty 配置](https://docs.astral.sh/ty/reference/configuration/)、
[ty 局部抑制](https://docs.astral.sh/ty/suppression/)。
实际 CLI 参数以本次固定版本的 `ty check --help` 为准；本次采集使用 gitlab JSON，未假定存在 `--output-format json`。
