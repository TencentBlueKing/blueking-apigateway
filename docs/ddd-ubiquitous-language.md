# BlueKing API Gateway DDD 统一概念词汇

本文是全仓库共享的统一语言（Ubiquitous Language），以 dashboard 控制面定义为主，记录各组件的语义映射。
本文区分当前实现、存量兼容与新增逻辑约定；具体行为须核对目标分支的源码与消费者，逐步下线是演进方向。

## 1. 使用约定

- 首次出现使用“中文名（English / 代码名）”；注明对象的网关、环境、版本或数据面范围，ID 使用具体字段名。
- 新代码、接口、文案、测试和评审使用下列规范词。新增逻辑统一使用 `gateway_id`、`gateway_name`；存量不可修改的数据库列、外键、数据和 Open API 字段保留 `api_id`、`api_name`，在边界映射。其他历史协议字段、枚举值和公开接口同样保持兼容。
- 改变共享概念时，在同一 PR 更新定义、身份范围、生命周期、消费者映射和源码入口；发现差异先核对拥有者与消费者。
- 本文不替代局部 `AGENTS.md` 的架构、运行与验证要求。纯文档改动检查差异、Markdown 和链接；代码改动按组件指南验证。

DDD 中，**限界上下文（Bounded Context）**指语义与规则的责任边界，不意味着独立部署或数据库。
**实体（Entity）**有持续身份；**值对象（Value Object）**按内容表达配置。
**聚合（Aggregate）**是业务一致性边界，不能把整个 Gateway 关系图视为一次事务；事务范围由用例决定。
**领域事件（Domain Event）**表达已发生事实；现有 PublishEvent 不代表已采用事件溯源或统一事件总线。
**上下文映射（Context Mapping）**明确不同表示间的转换，不要求把 ORM 模型改造成 DDD 类。

## 2. 上下文与组件职责

| 上下文 | 拥有者 | 边界 |
| --- | --- | --- |
| 网关定义与配置 | dashboard `core/`、`biz/` | 定义核心实体、配置和写入规则。 |
| 版本与发布 | dashboard `biz/resource_version`、`biz/release`、`controller/` | 制作快照、编排发布、编译 APISIX 原生配置并下发目标数据面。 |
| 运行配置同步 | operator | watch 控制面 etcd，解析校验、调度并差异同步原生配置到数据面 etcd，探测加载结果并上报；不编译 dashboard ORM 模型。 |
| 应用调用授权 | dashboard 管理；core-api 查询 | dashboard 写入申请与授权；core-api 查询、缓存并按已发布版本映射资源。APISIX 及插件执行请求鉴权。 |
| 管理访问控制 | dashboard `apps/rbac`、`biz/iam` | 用户的网关成员角色、操作权限及 IAM 协作。 |
| 发布事件接收 | core-api | 接收 operator 事件、关联 ReleaseHistory、去重落库；不发起发布。 |
| MCP 服务定义 | dashboard `apps/mcp_server`、`biz/mcp_server` | 定义服务、工具选择与别名、协议、扩展及应用权限。 |
| MCP 协议代理 | mcp-proxy | 加载定义与版本 OpenAPI 制品，生成工具、管理协议实例、检查访问权限并经网关调用 API。 |
| 产品交互 | dashboard-front | 通过控制面 API 展示编辑对象，适配 DTO；路由与 store 不重新定义领域概念。 |
| 数据面执行 | APISIX（独立仓库 `blueking-apigateway-apisix`） | 加载配置，执行匹配、认证、鉴权、插件与转发。 |

### Project Relationship

以下箭头表示请求、配置传播或数据库访问方向。

| 链路 | 项目与存储依赖 |
| --- | --- |
| API 管理与发布 | dashboard-front → dashboard ↔ MySQL；dashboard controller → 控制面 etcd → operator → 数据面 etcd → APISIX。 |
| 发布事件上报 | dashboard → MySQL（前三步事件）；operator → core-api → MySQL（后三步事件）；dashboard 读取事件并推进发布状态。 |
| API 调用权限 | dashboard → MySQL（申请/授权）；APISIX → core-api → MySQL（运行时权限查询，含缓存）。 |
| MCP 服务 | dashboard-front → dashboard → MySQL；mcp-proxy 从 MySQL 读取 MCP 定义、权限、Release 与版本 OpenAPI 制品，工具调用经 APISIX 转发。 |

dashboard、core-api、mcp-proxy 访问同一网关业务 MySQL 数据库；模型与配置写入规则以 dashboard 为主。
控制面 etcd 保存 dashboard 下发的配置，数据面 etcd 保存 operator 同步的 APISIX 配置；前端通过 dashboard API 访问控制面。

核对：[dashboard 模型](../src/dashboard/apigateway/apigateway/core/models.py)、
[core-api DAO](../src/core-api/pkg/database/dao/gateway.go)、
[MCP 数据映射](../src/mcp-proxy/pkg/entity/model/gateway.go)；发布、权限与 MCP 的消费者入口见第 4–6 节。

## 3. 控制面核心词汇

核对：[核心模型](../src/dashboard/apigateway/apigateway/core/models.py)、
[枚举](../src/dashboard/apigateway/apigateway/core/constants.py)、
[数据面模型](../src/dashboard/apigateway/apigateway/apps/data_plane/models.py)、
[租户规则](../src/dashboard/apigateway/apigateway/common/tenant/validators.py)。

| 中文 / English | 代码名与身份范围 | 定义与约束 |
| --- | --- | --- |
| 网关 / Gateway | `Gateway`；id；name 全局唯一 | 一组 API 的管理与发布归属，拥有环境、资源、后端等。 |
| 网关类别 / Gateway Kind | `Gateway.kind` | `normal`、`programmable`、`ai`；ORM 分别存 `0`、`1`、`2`，API 按 GatewayKindEnum/GatewayKindNameEnum 转换。与认证配置的网关类型区分。 |
| 网关弃用 / Gateway Deprecation | `is_deprecated`、`deprecated_note` | 弃用标记及原因，与启停、公开、官方、删除分别表达。 |
| 环境 / Stage | `Stage`；id；`(gateway, name)` 唯一 | 网关内的发布目标，如 prod、test，带变量、状态和环境配置；与 DataPlane 是不同维度。 |
| 环境变量 / Stage Variable | `Stage.vars` | 环境级键值，用于受支持的路径或配置渲染；可引用范围由配置契约决定，与进程环境变量区分。 |
| 资源 / Resource | `Resource`；id；归属 Gateway | 可编辑的 API 定义，含名称、方法、路径、类别与代理；不直接归属 Stage。 |
| 资源名称 / Resource Name | `Resource.name` | 网关内业务标识，用于快照、OpenAPI、MCP 映射；与主键、METHOD path、工具别名区分。写入边界校验网关内 name 唯一及 `(gateway, method, path)` 唯一，不能都称为 ORM 唯一约束。 |
| 资源类别 / Resource Kind | `Resource.kind` | `standard` 或 `ai`；缺少 kind 的历史快照按 standard 解释。 |
| 资源代理配置 / Resource Proxy | `Proxy`；`(resource, type)` 唯一 | `Resource.proxy_id` 选择代理，`Proxy.backend` 引用 Backend；与 mcp-proxy 和 ai-proxy 插件区分。 |
| 后端服务 / Backend | `Backend`；id；`(gateway, name)` 唯一 | 网关内可复用的后端身份；地址、超时等环境差异由 BackendConfig 表达。 |
| 后端类别 / Backend Kind | `Backend.kind` | standard 或 ai；普通 API/模型代理 API 关联对应类别后端。kind 与传输 type 区分。 |
| 后端环境配置 / Backend Configuration | `BackendConfig`；`(gateway, backend, stage)` 唯一 | 后端在环境中的配置：普通 hosts/timeout/loadbalance，或规范化 AI provider/instances 等。 |
| 作用域配置 / Context | `Context`；`(scope_type, scope_id, type)` 唯一 | **存量兼容**：经 schema 校验的网关、环境或资源配置，如认证，逐步弱化及下架；新增对象直接在代码中用对应 JSON Schema 校验，不扩展 Context。与请求上下文、Go context、限界上下文区分。 |
| 环境资源禁用 / Stage Resource Disabled | `StageResourceDisabled`；`(stage, resource)` 唯一 | **存量兼容**：仅存量网关使用，新产品已移除配置入口，逻辑将逐步弱化及移除；现有环境名称仍进入版本快照并参与路由过滤，不改变资源归属。 |
| 数据面 / Data Plane | `DataPlane`；id；name 唯一 | 有独立 etcd 配置、命名空间、访问地址模板与 APISIX 版本的发布目标。 |
| 网关数据面绑定 / Gateway–Data Plane Binding | `GatewayDataPlaneBinding` | 网关可绑定多个数据面；版本发布遍历绑定的活跃数据面。 |
| 租户 / Tenant | `tenant_mode`、`tenant_id`；调用者租户信息 | 网关模式 single/global 影响访问与隔离；租户与网关、应用、环境及其授权分别表达。 |

归属与引用（不表示创建顺序、事务边界或级联删除）：

- Gateway 拥有 Stage、Resource、Backend、BackendConfig、ResourceVersion；Resource 经 Proxy 引用 Backend。
- BackendConfig 同时引用 Gateway、Backend、Stage；Release 关联 Stage 与 ResourceVersion。
- Gateway 经 GatewayDataPlaneBinding 关联 DataPlane。不能使用 `Gateway -> Stage -> Resource` 作为模型归属链。

## 4. 版本、发布与运行态

| 中文 / English | 代码名 | 定义与边界 |
| --- | --- | --- |
| 资源版本 / Resource Version | `ResourceVersion` | 网关资源快照集合，含代理、资源 Context/插件、禁用环境等；可发布到多个环境。 |
| 版本号 / Version Label | `ResourceVersion.version` | 网关内创建时校验唯一的展示字符串；与主键 id、schema_version、APISIX 软件版本区分。 |
| 环境当前版本关联 / Release | `Release` | 每个 Stage 至多一条，引用 ResourceVersion；其主键不是每次发布流水号，关联存在也不证明数据面已加载。 |
| 已发布资源投影 / Released Resource | `ReleasedResource` | 按 `(gateway, resource_version_id, resource_id)` 保存的快照查询投影，不是草稿或数据面已加载的证明。 |
| 发布历史 / Release History | `ReleaseHistory` | 一次面向环境和数据面的发布过程，含 source、版本与数据面；正常发布每个目标数据面独立记录，历史 data_plane 可为空。 |
| 发布事件 / Publish Event | `PublishEvent` | 发布步骤、状态与详情；publish 外键指向 ReleaseHistory，持久化列为 publish_id。 |
| 发布输入 / Release Data | `controller.ReleaseData` | 资源快照结合当前网关、环境、BackendConfig、环境插件等得到的编译输入。 |
| 发布标记 / Release Marker | `controller.BkRelease`、etcd `_bk_release`、operator `ReleaseInfo` | 同步环境发布信息与 publish_id 的标记；与 ORM Release/ReleaseHistory 区分。 |
| APISIX 路由 / APISIX Route | controller/operator `Route` | 资源快照编译出的匹配、插件与 Service 引用；运行 ID、地址及附加路由由编译规则决定。 |
| APISIX 服务 / APISIX Service | controller/operator `Service` | 后端在环境中的 upstream/插件等运行配置，可被多个路由引用；与 Backend、代码层 service/ 区分。 |
| 上游 / Upstream | APISIX upstream | 普通后端转发与负载均衡配置；AI Service 可由模型代理插件调用而无普通 upstream。 |
| 插件元数据 / Plugin Metadata | APISIX `plugin_metadata` | 全局插件运行配置，operator 按全局资源同步；与 Stage PluginBinding 区分。 |

**快照边界**：修改 Resource、Proxy、资源插件不会改写既有版本。发布时读取的环境、BackendConfig 等可变，
所以相同 ResourceVersion 不保证完整运行配置相同；分析变更与回滚须同时考虑快照和当前配置。

**动作**：生成资源版本 / Create Resource Version 只制作快照；版本发布 / Publish Resource Version 选择版本、环境与数据面并编译下发；
配置重新下发 / Republish Configuration 可复用 Release 的版本；环境下架 / Disable Stage 停止环境运行配置。
删除 / Delete 须注明对象及清理流程，与下架分别表达。

标准发布链路：

```text
dashboard-front -> dashboard biz/release -> 每个目标数据面一条 ReleaseHistory
  -> dashboard controller -> 控制面 etcd -> operator -> 数据面 etcd -> APISIX
operator 同步/加载探测事件 -> core-api -> MySQL PublishEvent
  -> dashboard 发布成功回调；前端展示进度
```

- 步骤依次为配置校验、生成任务、下发、解析、应用、加载配置。前三步由 dashboard 产生并直接落库，后三步由 operator 上报、core-api 落库。
- 事件状态 pending/doing/success/failure；历史展示状态由最新事件与超时推导。下发或应用成功不等于最终加载成功；事件缺失或超时也可显示失败。
- 发布来源 `ReleaseHistory.source` / `PublishSourceEnum` 表达触发原因，与步骤、状态、版本类别区分。
- Gateway/Stage 的 ACTIVE=1、INACTIVE=0 是启停状态。Release 无数据面维度：首次发布预建关联，已有关联在成功回调更新；一个数据面成功即可触发更新。
- 每个数据面成功后，回调更新 Release/已发布投影、激活 Stage，并移除 MCP 中新版本标准资源集合已不包含的资源名；异步协调 MCP 权限，并尝试协调 OAuth2 内置应用权限。
- 判断全部数据面结果须检查各自 ReleaseHistory、事件与运行态。MySQL、两个 etcd 与 APISIX 异步传播，不保证跨组件原子提交或即时一致性。

核对：[快照制作](../src/dashboard/apigateway/apigateway/biz/resource_version/resource_version.py)、
[发布输入与插件名映射](../src/dashboard/apigateway/apigateway/controller/release_data.py)、
[发布编排](../src/dashboard/apigateway/apigateway/biz/release/gateway_releaser.py)、
[dashboard 发布事件落库](../src/dashboard/apigateway/apigateway/service/event/event.py)、
[配置重新下发](../src/dashboard/apigateway/apigateway/controller/publisher/publish.py)、
[成功回调](../src/dashboard/apigateway/apigateway/controller/tasks/release.py)、
[operator 同步](../src/operator/pkg/core/committer/committer.go)、
[加载探测](../src/operator/pkg/eventreporter/reporter.go)。

## 5. 认证、权限与管理角色

| 中文 / English | 代码名与范围 | 统一含义 |
| --- | --- | --- |
| 蓝鲸应用 / BlueKing Application | `bk_app_code` | API/MCP 调用应用身份，与 username、gateway_id、后端名区分。 |
| 认证 / Authentication | Context、JWT、OAuth2 等 | 验证应用或用户身份；与授权 / Authorization 的管理、API 调用、MCP 访问许可分别表达。 |
| 网关成员 / Gateway Member | `GatewayMember`；`(gateway, username)` 唯一 | 控制面管理角色 administrator/operator；角色 operator 与运行组件无关。 |
| 网关操作权限 / Gateway Action Permission | `GatewayActionEnum`、`GATEWAY_ROLE_ACTIONS` | 用户管理、运营、审批等权限，不能只根据历史 maintainers 判断。 |
| 应用网关调用权限 / App Gateway Permission | `AppGatewayPermission`；`(bk_app_code, gateway)` | 应用访问网关所有资源的限期授权，与管理员角色区分。 |
| 应用资源调用权限 / App Resource Permission | `AppResourcePermission`；`(bk_app_code, gateway, resource_id)` | 特定资源的限期授权；resource_id 非当前 Resource 的级联外键，兼容草稿删除而快照仍存在。 |
| 权限申请 / Permission Application | `AppPermissionApply`、`AppPermissionRecord` | 申请与处理记录；申请存在不等于有效授权。 |
| 运行时权限查询 / Runtime Permission Query | core-api `AppPermissionService.Query` | 通过 Stage 的 Release/ResourceVersion 将资源名映射为 ID，不能只查当前草稿。 |
| MCP 服务应用权限 / MCP Server App Permission | `MCPServerAppPermission`；`(bk_app_code, mcp_server)` | 特定 MCP Server 的应用授权，与工具 API 调用授权是两个检查边界。 |
| OAuth2 内置应用 / OAuth2 Built-in Application | public/personal 及 enabled 字段 | 内置客户端模式授权，由发布与权限协调流程维护。 |
| 公开可见 / Public Visibility | 各对象 `is_public` | 对象各自的公开范围，不能统一解释为匿名、免认证或免授权。 |

权限由 dashboard 写入；core-api DAO/缓存是运行时表示，缓存可能滞后。
权限通常不以 Stage 为授权键，查询参数 Stage 用于选择快照。
MCP 使用 `v_mcp_{mcp_server_id}_{app_code}` 虚拟应用调用工具 API，其 AppResourcePermission 由 dashboard MCP 权限流程同步。

核对：[调用权限模型](../src/dashboard/apigateway/apigateway/apps/permission/models.py)、
[RBAC 模型](../src/dashboard/apigateway/apigateway/apps/rbac/models.py)、
[角色动作](../src/dashboard/apigateway/apigateway/apps/rbac/constants.py)、
[core-api 权限查询](../src/core-api/pkg/service/app_permission.go)、
[OAuth2 权限协调](../src/dashboard/apigateway/apigateway/controller/tasks/oauth2_builtin.py)。

## 6. 插件、接口制品与 MCP

| 中文 / English | 代码名 | 统一含义 |
| --- | --- | --- |
| 插件类型 / Plugin Type | `PluginType`；code | 类型、作用域与配置 schema；code 是控制面类型标识，发布时可按作用域映射 APISIX 名，如 bk-rate-limit → bk-stage-rate-limit / bk-resource-rate-limit。 |
| 插件配置 / Plugin Configuration | `PluginConfig` | 网关内的类型配置实例，与原生插件配置和 PluginMetadata 区分。 |
| 插件绑定 / Plugin Binding | `PluginBinding`；scope_type/scope_id/config | 将配置应用到环境或资源；资源绑定入快照，环境绑定发布时读取，绑定与合并遵循作用域/类别规则。 |
| 资源接口协议 / Resource OpenAPI Schema | `OpenAPIResourceSchema` | 可编辑请求/响应协议，与配置校验 Schema、文本资源文档区分。 |
| 接口协议版本 / OpenAPI Schema Version | `OpenAPIResourceSchemaVersion` | 与 ResourceVersion 关联的接口协议快照。 |
| 版本 OpenAPI 制品 / Versioned OpenAPI Specification | `OpenAPIFileResourceSchemaVersion`；`openapi_gateway_resource_version_spec` | 版本关联的完整 OpenAPI 文件，供 MCP 等消费。 |
| 资源文档 / Resource Documentation | `ResourceDoc`、`ResourceDocVersion`、`ReleasedResourceDoc` | 使用说明及版本/已发布投影，与机器协议分别维护。 |
| 网关 SDK / Gateway SDK | `GatewaySDK` | 可关联资源版本的 SDK 制品，包版本与 publish_id、APISIX 版本区分。 |
| 操作审计事件 / Audit Event | `AuditEventLog` | 操作者、对象、动作与前后数据，与发布事件、访问日志、trace 区分。 |
| MCP 服务 / MCP Server | `MCPServer`；name 全局唯一；gateway/stage | 将所选环境 API 暴露为工具；跟随 Stage 的 Release，不独立绑定版本。 |
| MCP 工具 / MCP Tool | resource_names/tool_names | 版本普通资源的协议映射，不创建新 Resource；resource_name@tool_name 表达别名，默认使用资源名。 |
| MCP 提示模板 / MCP Prompt | `MCPServerExtend(type=prompts)` | 服务扩展中的提示模板，与工具、后端 provider、API 请求体区分。 |
| MCP 协议类型 / MCP Protocol Type | protocol_type | SSE / Streamable HTTP，与 Backend.type、Resource.kind 区分。 |
| MCP 原始响应模式 / Raw Response Mode | raw_response_enabled | 工具结果返回原始 API 响应体，不改变身份、授权或版本选择。 |

MCP 候选资源来自活跃 Stage 的 Release 所引用版本，筛选 kind=standard（旧快照缺 kind 按 standard），排除 AI 资源。
**存量兼容：当前候选校验不筛选 disabled_stages；APISIX Route 编译仍跳过历史快照中该环境禁用的资源。候选合法不保证工具 API 在目标环境可调用。**
mcp-proxy 按原资源名选择版本 OpenAPI operation、按别名暴露工具，再经网关调用；别名变化不改变资源 ID 或权限归属。
MCP 协议的 resources 能力与网关 Resource/MCP Tool 是不同概念。

核对：[插件模型](../src/dashboard/apigateway/apigateway/apps/plugin/models.py)、
[OpenAPI 模型](../src/dashboard/apigateway/apigateway/apps/openapi/models.py)、
[文档与 SDK](../src/dashboard/apigateway/apigateway/apps/support/models.py)、
[审计模型](../src/dashboard/apigateway/apigateway/apps/audit/models.py)、
[MCP 模型](../src/dashboard/apigateway/apigateway/apps/mcp_server/models.py)、
[MCP 校验与权限同步](../src/dashboard/apigateway/apigateway/biz/mcp_server/mcp_server.py)、
[候选类别筛选](../src/dashboard/apigateway/apigateway/service/resource_version/schema.py)、
[环境禁用路由过滤](../src/dashboard/apigateway/apigateway/controller/convertor/route.py)、
[代理加载](../src/mcp-proxy/pkg/mcp/mcp.go)、
[工具转换](../src/mcp-proxy/pkg/infra/proxy/converter.go)。

## 7. AI 后端与表示边界

模型服务 / AI Backend 是 `Backend(kind=ai)`；模型代理 API / AI Resource 是 `Resource(kind=ai)`，复用现有代理关系。
AI Gateway 也可含普通后端/资源；不能以 Gateway.kind 代替子对象 kind。

| 中文 / English | 表示 | 约定 |
| --- | --- | --- |
| 模型厂商 / Provider | AIBackendConfig | 存储值为 openai、deepseek、openai-compatible；前两者发布时转为 openai-compatible 并使用注册表 endpoint，自定义 openai-compatible 要求并保留 override.endpoint。 |
| 模型实例配置 / AI Backend Instance | AIBackendConfig.instances | provider/auth/options/override 等配置，不是独立数据库实体或进程实例。 |
| 模型名 / Model Name | instance options.model 等 | 厂商模型标识，与 Backend.name、Resource.name、工具名区分。 |
| Web 配置 / Web DTO | `AIBackendWebConfigAdapter` | 扁平前端表示，经边界适配；布局、掩码、输入限制不成为核心存储定义。 |
| 规范化存储配置 / Stored Configuration | `core.backend_config.AIBackendConfig`、BackendConfig | 类型化存储契约；AI 配置在 ORM 持久化边界加密，不以 DTO 或发布结构绕过写入。 |
| 运行插件配置 / Published Plugin Configuration | controller AI Service 转换 | 编译 ai-proxy/ai-proxy-multi，适配 provider/endpoint/timeout 等。 |

核对：[Web 适配](../src/dashboard/apigateway/apigateway/apis/web/ai_backend/adapter.py)、
[规范化配置](../src/dashboard/apigateway/apigateway/core/backend_config.py)、
[厂商注册表](../src/dashboard/apigateway/apigateway/core/ai_backend.py)、
[Service 编译](../src/dashboard/apigateway/apigateway/controller/convertor/service.py)。

## 8. 跨组件标识与历史名称

| 标识 | 规范含义与边界 |
| --- | --- |
| gateway_id；兼容 api_id/core_api | 新增逻辑使用 gateway_id 表达 Gateway 主键；api_id 与表名 core_api 仅为存量兼容。“API”指接口时须明确 Resource，不能由 api_id 推断单个接口。 |
| gateway_name；兼容 api_name/{api_name} | 新增逻辑使用 gateway_name 表达 Gateway.name；api_name 及历史地址/模板占位符仅为存量兼容，与 Resource.name 区分。 |
| 前端 apigwId | 相关网关接口的 Gateway.id；按 services/source 请求路径核对。 |
| stage_id/stage_name | Stage 主键/网关内环境名；同名环境可属不同网关。 |
| resource_id/resource_name | 资源主键/业务名；权限、版本、MCP 按所用快照映射，与 APISIX resourceID 区分。 |
| resource_version_id | ResourceVersion.id，供 Release、OpenAPI、权限映射、MCP 引用。 |
| _bk_release.resource_version / operator ReleaseInfo.ResourceVersion | ResourceVersion.version 字符串。 |
| dashboard release_id | Release.id，环境当前版本关联主键。 |
| operator release_id / _bk_release.id | bk.release.{gateway}.{stage}，运行环境复合标识，与数值 Release.id 区分。 |
| 正常 publish_id/PublishID/PublishId | ReleaseHistory.id，发布、标签、事件共同关联键，与 Release.id、版本 ID、事件 ID 区分。 |
| publish_id=-1 / -2 | 分别为无需上报同步 / 删除发布标记；operator 对 -1、-2 和空 publish_id 均不上报发布事件。 |
| publish_id=-3 | dashboard GLOBAL_PUBLISH_ID，全局资源下发保留值；不是 operator 定义的普通环境发布 ID。 |
| validata_configuration | 持久化的“配置校验”事件历史拼写，生产者/消费者保持兼容。 |
| scope_type | ScopeTypeEnum/ContextScopeTypeEnum：api（网关历史值）、stage、resource。 |
| Context.type | ContextTypeEnum：api_auth、resource_auth、stage_proxy_http、api_feature_flag；配置类型，与作用域字段区分。 |

保留 publish_id 不是 ReleaseHistory 主键；其他空值/零值行为按所属路径核对。
operator/APISIX 用 gateway.bk.tencent.com/{gateway,stage,publish-id,apisix-version} 标签传递归属与发布信息；
数据面 etcd 按 routes/services 等类型平铺，不能从 key 层级推导 Stage 所有权。

核对：[core-api DAO](../src/core-api/pkg/database/dao/gateway.go)、
[事件关联](../src/core-api/pkg/service/publish_event.go)、
[operator 标识与标签](../src/operator/pkg/entity/entity.go)、
[operator 保留 ID](../src/operator/pkg/constant/event.go)、
[dashboard 保留 ID](../src/dashboard/apigateway/apigateway/controller/constants.py)、
[全局下发](../src/dashboard/apigateway/apigateway/controller/tasks/syncing.py)、
[前端发布映射](../src/dashboard-front/src/services/source/release.ts)。
