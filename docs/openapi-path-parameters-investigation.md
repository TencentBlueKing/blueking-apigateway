# OpenAPI 导入的路径参数与共享 parameters 复核

复核日期：2026-11-24。源码基线：`8f30c8c4769d6425c5308ccbad12435a169e628b`。

针对本次 OpenAPI 3 场景，**Path Item 层的共享 `parameters` 确实会丢失。** 当前实现只把 HTTP operation 传给资源解析器，
operation 不继承共享参数。已明确声明的参数类型、必填、描述和示例因此无法进入资源接口协议，
再次使用 OpenAPI 导出器导出时也无法恢复。没有找到将此丢弃行为定义为兼容约定的源码依据，
结合标准和对照复现，应按解析遗漏处理；这不证明历史作者的主观意图。

这份文档回答现状与设计依据的复核问题，记录后续修复的验收条件；不改变生产解析行为。
共享概念仍以 [DDD 统一语言](ddd-ubiquitous-language.md) 为准。

## 两种“路径参数”的区别

| 项目 | OpenAPI 3.0 | 当前网关约定与实现 |
| --- | --- | --- |
| 路径模板 | 使用 `{id}`，参数名大小写敏感 | 使用相同的 `{id}` 写法，例如 `/users/{id}/`；导入保留模板 |
| 路径参数声明 | 模板变量必须有对应的 `in: path` 参数，`required: true` | 导入校验有意放宽模板参数声明的检查，允许省略；这属于兼容行为 |
| 参数名限制 | 要求与模板变量对应 | Web 创建、编辑及标准化导入要求 ASCII 字母开头，后续为字母、数字或下划线，最多 30 字符；同一路径内不能重名 |
| Path Item `parameters` | 适用于该路径下的所有 operation；可以包含 path、query、header、cookie 参数 | 当前在方法过滤时丢弃；不等同于 `in: path` 参数 |
| operation `parameters` | 按 `(name, in)` 覆盖共享参数，不能删除继承项；同名不同位置是不同参数 | 当前只保存 operation 自己的参数；共享项不参与合并 |
| 后端路径变量 | 标准描述接口路径，不定义网关转发配置 | 网关后端路径支持普通变量及 `{env.name}` 环境变量；后者是网关配置约定 |

标准依据：[OAS 3.0.3 Path Templating](https://spec.openapis.org/oas/v3.0.3.html#path-templating)、
[Path Item Object](https://spec.openapis.org/oas/v3.0.3.html#path-item-object)、
[Operation Object](https://spec.openapis.org/oas/v3.0.3.html#operation-object)、
[Parameter Object](https://spec.openapis.org/oas/v3.0.3.html#parameter-object)。
`/orders` 路径下共享的 query 参数 `page` 同样会丢失，即使 URL 中没有 `{...}`。

## 当前调用链与设计证据

- Web 导入页 [settings/import/Index.vue](../src/dashboard-front/src/views/resource-management/settings/import/Index.vue)
  将源文件传给预检，之后将预检返回的资源字段提交到标准化导入 API。
  [ResourceImportCheckApi](../src/dashboard/apigateway/apigateway/apis/web/resource/views.py)
  调用 `OpenAPIImportManager.validate()`；因此前端预览拿到的协议已经缺共享参数。
- [legacy Open](../src/dashboard/apigateway/apigateway/apis/open/resource/views.py) 与
  [V2 Sync](../src/dashboard/apigateway/apigateway/apis/v2/sync/views.py) 都调用
  [sync_openapi_resources_from_content](../src/dashboard/apigateway/apigateway/biz/resource/importer/sync.py)，
  使用同一导入管理器，之后交由资源导入器保存。
- [OpenAPIImportManager](../src/dashboard/apigateway/apigateway/biz/openapi/openapi.py) 解析文档内部引用后按版本选择解析器：
  Swagger 2.0（`OPENAPIV2`）使用 [BaseParser](../src/dashboard/apigateway/apigateway/biz/openapi/parser.py)，
  OpenAPI 3.0/3.1 使用其子类 `OpenAPIV3Parser`。两者共用
  `get_resources → get_paths → _remove_invalid_method`，只保留方法白名单。
  `Path Item.parameters` 在调用 `_get_openapi_schema` 前消失；后者仅读取 operation 的字段。
- [ApigwOperationValidator](../src/dashboard/apigateway/apigateway/biz/openapi/schema.py) 的注释和实现明确放宽
  路径参数声明检查；导入管理器也排除 `UnresolvableParameterError`。这解释省略声明的兼容性，
  无法解释丢弃已经声明的参数。OpenAPI 3 解析器也不会自动补出被丢弃参数的原始元数据。
- 路径写法的 UI 依据是 [FrontConfig.vue](../src/dashboard-front/src/views/resource-management/components/FrontConfig.vue)。
  名称与后端变量限制见 [PathVarsValidator / BackendPathVarsValidator](../src/dashboard/apigateway/apigateway/apis/web/resource/validators.py)
  和 [常量](../src/dashboard/apigateway/apigateway/apis/web/resource/constants.py)。这些限制适用于 Web 校验入口，
  不应据此断言 Open/V2 Sync 对变量名做了完全相同的校验。
- [ResourcesSaver](../src/dashboard/apigateway/apigateway/biz/resource/savers.py) 保存解析后的接口协议。
  [BaseExporter](../src/dashboard/apigateway/apigateway/service/resource_version/openapi_export.py) 将协议写入 operation；
  不会恢复共享参数。[资源文档解析器](../src/dashboard/apigateway/apigateway/biz/resource_doc/importer/parsers.py)
  的原始文件入口也消费 `parser.get_paths()`，Web 文档入口则消费标准化 DTO，因此两者都有丢失链路。

Swagger 2.0 也会丢失共享参数：`BaseParser` 只从 operation 读取 path/query/header 参数，
并将 operation 的 `body/formData` 参数转换为 `requestBody`；共享请求体参数不会进入该转换。
与 OpenAPI 3 分支不同，当 operation 没有 `parameters` 键时，它会通过
[extract_openapi_parameters_from_path](../src/dashboard/apigateway/apigateway/utils/openapi.py)
从路径模板补出 string 类型、必填、空描述的路径参数，但不能恢复共享参数的原始元数据。
显式 `parameters: []` 不触发补全。这一分支说明来自源码核对，下方复现和额外隔离检查均针对 OpenAPI 3。

## 可运行复现

在 `src/dashboard` 的已锁定 EE 环境中运行。样例加载真实 Django 设置、生产解析器和 OpenAPI 导出器，
不访问数据库。断言刻画本次基线的缺陷现状，不能作为修复后的预期结果。

```bash
uv run bash <<'SH'
cd apigateway
. apigateway/conf/unittest_env
export DJANGO_SETTINGS_MODULE=apigateway.settings
python - <<'PY'
from copy import deepcopy
import json
import django
django.setup()
from apigateway.biz.openapi import OpenAPIV3Parser
from apigateway.service.resource_version import BaseExporter

shared = [
    {"name": "id", "in": "path", "required": True,
     "description": "Order identifier", "schema": {"type": "integer"}, "example": 42},
    {"name": "page", "in": "query", "required": False,
     "description": "Shared page", "schema": {"type": "integer"}, "example": 2},
]
data = {
    "openapi": "3.0.3", "info": {"title": "Orders", "version": "1.0"},
    "paths": {"/orders/{id}": {
        "parameters": shared,
        "get": {"operationId": "get_order", "responses": {"200": {"description": "OK"}}},
    }},
}
parser = OpenAPIV3Parser(deepcopy(data))
resources = parser.get_resources()
assert list(parser.get_paths()["/orders/{id}"]) == ["get"]
assert resources[0]["path"] == "/orders/{id}"
assert "parameters" not in resources[0]["openapi_schema"]
exporter = BaseExporter(include_bk_apigateway_resource=False)
exported = json.loads(exporter.to_openapi(deepcopy(resources), "json"))
assert "parameters" not in exported["paths"]["/orders/{id}"]["get"]

# 将同一参数显式放到 operation 上，元数据可以保留和导出。
data["paths"]["/orders/{id}"]["get"]["parameters"] = deepcopy(shared)
resources = OpenAPIV3Parser(data).get_resources()
assert resources[0]["openapi_schema"]["parameters"] == shared
exported = json.loads(exporter.to_openapi(deepcopy(resources), "json"))
assert exported["paths"]["/orders/{id}"]["get"]["parameters"] == shared
print("Confirmed: shared parameters lost; explicit operation parameters retained")
PY
SH
```

额外隔离检查使用当前自定义校验器与 Prance 引用解析器，观察到：仅路径级声明丢失；operation
覆盖项及同名 header 保留但共享 `id/path` 丢失；operation 的空数组也丢失继承项；显式 operation
声明完整保留；文档内部 `$ref` 解引用后的共享项仍丢失；省略声明被接受且模板保留；仅共享 query
参数的 `/orders` 同样丢失。这些是现状复现，不是修复回归测试。

## 后续修复的验收边界

以下验收首先针对原请求的 OpenAPI 3 场景。

建议在解析时将共享参数合并到各 operation，按 `(name, in)` 保留或覆盖；方法遍历仍只处理 operation。
需验证多方法继承、同名同位置覆盖、同名不同位置保留、空数组不能删除继承项、内部引用、输入不被修改，
以及导入保存后再次 OpenAPI 导出。保留允许省略路径参数声明的现有兼容行为；若要改为严格校验，应单独确认兼容影响。
文档解析器直接消费 `get_paths()`，修复方案也必须保证该消费者收到有效 operation 和合并后的参数。

若后续修复修改两版本共用的 `get_paths()` 过滤逻辑，还需明确 Swagger 2.0 的兼容验收范围：
共享 path/query/header 元数据、共享 `body/formData` 到 `requestBody` 的转换，以及缺少 operation
`parameters` 键时的模板变量补全与显式空数组行为。本文未完成 Swagger 2.0 的导入保存和往返导出验收，
是否同批修复应在后续请求中确定。

本次验证覆盖解析、引用解析、自定义标准校验和内存导出；数据库保存与文档生成影响来自上述源码链路。
未执行真实 MySQL、浏览器导入、APISIX 路由调用或 SDK/MCP 使用验证，也未把协议参数类型解释为数据面校验规则。
本次仅新增 Markdown，按仓库规则检查文档差异、引用与可执行样例，不运行应用 lint/test/build 全量门禁。
