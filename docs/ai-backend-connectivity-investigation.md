# 模型服务 Models Endpoint 与连接测试调查

对应问题：#3392。本文记录当前代码行为、方案取舍和建议的验收条件；行为调整仍需另行实施。

## 结论与建议

建议保留 Models Endpoint 选填，将拉取模型列表与保存配置解耦。
当前“连通测试”通过请求 Models API 获取模型列表，却被页面作为保存的前置条件。
这使模型列表接口成为隐含必填能力：即使用户提供了可用的 Chat Completions 地址，
只要模型列表地址无法推导或请求失败，就无法通过页面保存。

把 Models Endpoint 改成必填、或提前展示推导地址，只能让这个依赖更明显，
不能解决上游没有模型列表接口的情况。保存应验证配置是否合法；拉取模型列表应是辅助操作，
失败时允许手动填写 Model，或保留现有的空值语义，由调用方指定 model。

## 当前调用链与证据

| 环节 | 当前行为 | 代码位置 |
| --- | --- | --- |
| 输入 | Models Endpoint 无必填规则；Model 支持手动输入和留空。 | [AIBackendConfigForm.vue](../src/dashboard-front/src/views/model-services/components/AIBackendConfigForm.vue)：Models Endpoint、Model 表单项 |
| 请求 | `handleTest` 调用 `testBackendServiceConnection`，成功后保存返回的模型列表与配置快照。 | [AIBackendConfigForm.vue](../src/dashboard-front/src/views/model-services/components/AIBackendConfigForm.vue)、[backend-services.ts](../src/dashboard-front/src/services/source/backend-services.ts) |
| API | `BackendConnectivityTestApi.post` 校验输入后调用 `get_ai_backend_model_ids`。 | [views.py](../src/dashboard/apigateway/apigateway/apis/web/backend/views.py)、[serializers.py](../src/dashboard/apigateway/apigateway/apis/web/backend/serializers.py) |
| 地址选择 | 内置 Provider 使用注册表地址；自定义 Provider 优先使用显式 `model_endpoint`，否则从 completion 地址推导。 | [connectivity.py](../src/dashboard/apigateway/apigateway/biz/backend/connectivity.py)：`_get_endpoint_pair`；[ai_backend.py](../src/dashboard/apigateway/apigateway/core/ai_backend.py) |
| 实际探测 | 解析并检查两个地址的主机，随后仅对模型列表地址执行 HTTP GET；不调用 Chat Completions。响应须为 `data` 列表，每项含字符串 `id`。 | [connectivity.py](../src/dashboard/apigateway/apigateway/biz/backend/connectivity.py)：`get_ai_backend_model_ids`、`_resolve_endpoint` |
| 模型服务保存 | `canSubmit` 要求每个环境的 `isAIBackendConfigTestPassed` 为真，未测试、失败或快照不匹配都会禁用保存。 | [AddModelService.vue](../src/dashboard-front/src/views/model-services/components/AddModelService.vue)、[ai-backend-config.ts](../src/dashboard-front/src/views/model-services/utils/ai-backend-config.ts) |
| 环境保存 | `validateForms` 用同一函数检查 AI 后端，有未通过测试的配置时拒绝提交。 | [CreateStage.vue](../src/dashboard-front/src/views/stage-management/overview/components/CreateStage.vue) |
| 后端保存 | Web 字段和规范化配置允许省略 `model_endpoint`；创建、更新分别走配置校验与 `BackendHandler`，不调用连接测试。 | [Web serializers.py](../src/dashboard/apigateway/apigateway/apis/web/ai_backend/serializers.py)、[backend_config.py](../src/dashboard/apigateway/apigateway/core/backend_config.py)、[backend.py](../src/dashboard/apigateway/apigateway/biz/backend/backend.py) |
| 运行配置 | 编译 AI 插件配置时移除 `model_endpoint`，它不参与模型代理调用。 | [service.py](../src/dashboard/apigateway/apigateway/controller/convertor/service.py)：`_build_published_ai_instance` |

`createEditAIBackendConfigFormData` 会把已有配置初始化为 `success` 并建立快照，
没有发起测试请求。因此页面上的成功状态还可能只是“配置已保存”，不能作为实际连通性的证明。

### 自动推导和失败分支

推导是路径替换，不是发现上游能力。仅当路径以 `/chat/completions` 结尾时，
将该后缀替换为 `/models`；保留查询参数，移除 fragment。例如：

| Completion 地址 | 推导结果 |
| --- | --- |
| `https://llm.example.com/v1/chat/completions` | `https://llm.example.com/v1/models` |
| `https://llm.example.com/chat/completions` | `https://llm.example.com/models` |
| `https://llm.example.com/v1/chat/completions?api-version=2026-01-01#fragment` | `https://llm.example.com/v1/models?api-version=2026-01-01` |
| `https://llm.example.com/v1/generate` | 无法推导，不发起模型列表请求 |

推导成功只说明构造出了地址。若请求返回失败或响应结构不符合模型列表契约，
推导分支同样抛出 `AIBackendModelEndpointRequiredError`，页面得到“请配置 model_endpoint”提示。
它无法区分路径不匹配与推导后的接口不可用；填写显式地址后仍可能失败。
显式地址和内置 Provider 的请求失败走 `AIBackendConnectivityError`；
地址不安全或无法解析走 `AIBackendEndpointError`。当前实现不会在列表请求失败后尝试其他接口。

这些行为已有测试源码覆盖：

- [test_connectivity.py](../src/dashboard/apigateway/apigateway/tests/biz/backend/test_connectivity.py)：推导、无法推导、推导请求失败且无 fallback、显式 Models Endpoint、内置 Provider、响应结构和地址检查。
- [test_views.py](../src/dashboard/apigateway/apigateway/tests/apis/web/backend/test_views.py)：Web 错误响应及显式地址请求。
- [test_serializers.py](../src/dashboard/apigateway/apigateway/tests/apis/web/ai_backend/test_serializers.py)：自定义 Provider 可省略认证、Model 和 Models Endpoint。
- [test_backend_config.py](../src/dashboard/apigateway/apigateway/tests/core/test_backend_config.py)：兼容缺少 `model_endpoint` 的已存配置。
- [test_service.py](../src/dashboard/apigateway/apigateway/tests/controller/convertor/test_service.py)：发布配置不包含 `model_endpoint`。

以上是源码证据，不代表本次调查执行了应用测试或访问了真实上游。

## 方案比较

| 方案 | 能解决什么 | 代价与局限 | 建议 |
| --- | --- | --- | --- |
| Models Endpoint 改为必填 | 消除“选填却必须提供”的表单歧义。 | 仍要求上游提供列表接口；没有接口的用户仍无法保存。若扩大到存储或 API 契约，还会影响历史配置及同步客户端。 | 不作为根因修复。 |
| 提前推导并展示，改为必填 | 用户能看到测试将访问哪个地址，也能更早修改它。 | 推导结果不保证接口存在；必填仍不能支持没有列表接口的上游。自动写入还需处理用户覆盖、地址变化和旧配置回显。 | 可将推导预览作为列表功能的体验改善，保持选填。 |
| 用其他 Endpoint 做连接测试 | 若显式执行 completion 请求，可检验实际模型调用。 | 当前 Model 可留空；真实调用需要测试模型和请求内容，可能产生推理消耗。任意 GET、HEAD 或 TCP 成功无法证明模型调用成功，不能直接替换并沿用成功语义。 | 若需要真实调用验证，提供单独、显式的测试操作。 |
| 保存与拉取模型列表解耦 | 支持只有 completion 接口的上游；列表不可用也可保存合法配置。 | 保存成功不保证上游可用，需要明确结果含义和调用验证入口。 | 推荐，最直接消除隐含依赖。 |

## 建议的行为与验收条件

1. 将当前操作明确命名为“拉取模型列表”。Models Endpoint 保持选填，说明空值时会尝试推导；
   非标准 completion 路径提示可手动填写列表地址。上游无列表接口时允许继续手动填写 Model 或留空。
2. 模型服务页面和环境管理页面均以配置校验控制保存，不依赖列表请求状态或测试快照。
   校验仍覆盖必填 completion 地址、内置 Provider 凭据、认证字段配对、URL、参数和超时；
   已填写的非法 Models Endpoint 仍应报错。
3. 列表请求失败提示“无法获取模型列表”，区分无法推导与请求失败；
   不能仅根据列表请求失败断言 completion 不可用。成功应表示“模型列表获取成功”，
   已有配置回显也不应凭空显示完成了实际连接测试。
4. 保持存储、Open/Sync API 的选填契约及发布时移除 `model_endpoint` 的行为。
   若展示推导地址，优先作为预览，避免无意写入旧配置；继续保留地址检查、响应校验与错误信息脱敏。
5. 如另行需要真实连通测试，要求用户显式选择或输入测试模型并提交测试请求，说明会发起模型调用。
   成功结果仅代表当次选定模型请求成功；列表拉取和保存仍分别报告结果。

行为调整至少应验证：标准路径推导成功、推导列表不存在、路径无法推导、显式列表地址失败、
只有 completion 接口、Model 留空、内置 Provider、非法配置、编辑与克隆、
以及环境管理入口。列表请求未执行或失败时，合法配置仍应能在两个入口保存；
Model 留空时仍由调用方提供；非法配置仍拒绝提交。
