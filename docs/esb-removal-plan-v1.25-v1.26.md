# ESB 下线与存量兼容方案（1.25 / 1.26）

日期：2026-09-08

状态：方案报告，尚未实施或完成实际升级验证。

## 1. 目标与边界

**版本范围修正：本报告的 ESB 下线、新安装无 ESB、管理接口删除和认证迁移均针对 EE。TE 的 ESB 独立部署，TE Dashboard 原有权限申请、续期、记录查询、文档中心和 SDK 展示能力必须保持不变。公共代码不能按 ESB 名称整目录删除；下文涉及公共目录的删除项，均须先完成本节的 TE 依赖隔离。**

### 1.1 TE 保留边界与实际依赖

2026-09-08 补充调查确认：TE 的数据模型独立，但权限和文档业务实现尚未与公共代码完全隔离。

- `editions/te` 实际链接到独立仓库 `blueking-apigateway-te/src/dashboard/editions/te`；当前分支 `refactor/remove-sdk-edition-overrides`，提交 `1edcd3ae86f7fe04b1e80b4f26dba16f702fde20`。后续迁移到 TE 目录属于跨仓库交付。
- `te_default.py` 设置 `USE_GATEWAY_BK_ESB_MANAGE_COMPONENT_PERMISSIONS = False`。
- 公共 `biz/esb/permissions.py` 的 `ComponentPermissionManager.get_manager()` 因此选择 `ComponentPermissionByEsbManager`，直接使用 TE ESB 权限模型。不能删除此实现或其公共基类。
- TE 模型使用 `component_system_new`、`component_profile`、`app_component_perm`、`app_apply_perm_record`、`component_api_doc` 等表；`ComponentResourceBinding` 和 `AppPermissionApplyStatus` 为 `None`。这与 EE 通过网关资源映射管理权限的实现不同。
- TE 的 `apps/esb/urls.py` 为空，不代表没有 ESB 接口。权限入口位于公共 `apis/open/urls.py`、`apis/v2/inner/urls.py`；文档入口位于公共 `apis/web/docs/urls.py`。
- 公共文档 API 使用 `ComponentSystem`、`SystemDocCategoryHandler`、board 配置等。删除公共 `biz/esb` 或文档 API 会破坏 TE。
- 前端仍存在公共 ESB 文档页面、服务调用和功能开关；TE 模型独立不能保护这些前端资产免受删除影响。

### 1.2 建议的代码归属

| 内容 | EE 1.26 | TE 1.26 | 实现要求 |
| --- | --- | --- | --- |
| 内置 ESB 运行服务、注册和发布命令 | 删除 | 外部 ESB 不受影响 | 不删除 TE 自有集成命令或配置 |
| EE `bkcore` 模型及网关权限映射实现 | 删除不再需要的实现 | 保留 TE 自有模型、迁移和 manager | 先拆除公共模块对 EE 类和符号的导入依赖 |
| Open/V2 Inner ESB 权限接口及序列化器 | 不注册、不发布 | 原路径和请求响应保持 | 专用实现迁入 TE overlay；公共聚合 URL 保留版本扩展入口 |
| ESB 文档、SDK API 及业务辅助代码 | 不提供 | 保留原行为 | 将 TE 仍需的专用依赖闭包迁入 TE，通用依赖继续共享 |
| Django app、数据库、DB router、board/SDK 配置 | 不加载 ESB | 保留原配置与初始化效果 | 不能在公共配置中直接删除后不为 TE 补回 |
| API 网关资源 YAML 和接口文档 | 不再发布 EE ESB 接口 | 保留 TE 原接口定义与发布 | 检查同步命令的删除行为，防止 TE 升级自动撤销接口 |
| 前端 ESB 文档及相关调用/类型 | 不展示、不访问 | 保持原入口与展示 | 共用前端先保留资产，按版本能力控制；仅确认 EE 独占的页面可删 |
| 登录认证与通知 | 迁移到 EE 目标网关 | 保持 TE 当前行为 | 不全局清理 TE 使用的 URL、SDK 或认证覆盖 |

推荐最终将仅 TE 使用的后端 ESB 实现归入 TE overlay，保持激活后的 `apigateway.apis...`、`apigateway.biz...` 等运行导入路径和外部 URL 不变。不要让公共运行代码直接依赖 `apigateway.editions.te`：当前构建先通过 `editionctl activate --linker-type copy TE` 合成运行代码，再清理 `editions` 目录。

迁移不应复制整份公共 `urls.py` 或 `default.py` 来保存少数 TE 入口；应使用小粒度版本扩展模块，并在实际 editionctl 合成结果中验证。不应一次性搬走仍有非 ESB 消费者的公共工具、权限状态枚举或通用组件。

### 1.3 实施顺序与 TE 验收

1. 固定 TE 当前路由、请求响应、鉴权、权限数据写入和文档展示基线。
2. 在 TE 仓库补齐需迁移的实现、配置和接口定义，再完成公共注册点的版本隔离；协调两个仓库的版本组合，避免公共代码先删导致 TE 构建失败。
3. 分别构建 EE/TE，检查 edition 激活后的文件、导入、URL、app、数据库配置和接口发布定义。不要在当前工作区直接切换 edition 破坏其他未提交工作。
4. 验证 TE 权限申请写入原表，续期、列表、申请记录详情和原审批链路保持；验证文档 board、系统、组件详情和 SDK 展示/下载；不改变权限有效期及认证语义。
5. 验证 TE 前端入口和接口调用不变、升级不撤销已有 API 资源；EE 不再暴露相关接口。
6. TE 通过后再删除 EE 专用及已迁出的公共实现，做旧符号、导入、动态注册和测试引用扫描。

本次只确认了主要源码依赖，并未完成全部 TE 消费者清单、镜像构建、审批外部系统或页面运行验证。

### 1.4 EE 下线目标

1. 网关 1.25 的 Helm Chart 发布中公告 ESB 即将下线，并完成存量迁移准备。
2. 网关 1.26 删除 ESB 服务模块、管理能力、自动注册与主 Chart 中的 ESB 专用逻辑。
3. 全新部署不创建 ESB 服务、数据库、内置 ESB 网关、兼容 Ingress 或 ESB 兼容路由。
4. 已部署环境保留 ESB 运行资源、数据库表、配置、密钥和已有网关发布数据，使存量 compapi 流量继续通过网关代理。
5. `/api/c/self-service-api/` 和 `bk-esb-buffet` 不在保留兼容范围内，相关代理能力正式删除。

“保留存量配置”指保留继续运行所需的数据与配置；明确要求删除的 buffet 路由除外。不执行额外的存量数据库清理，不将代码删除自动转换成删除数据库记录的操作。

## 2. 已确认决策

| 决策 | 落地要求 |
| --- | --- |
| 删除 `bk-esb-buffet` | 删除代码库中的专用逻辑、初始化、配置和文档引用；实际实现前完成引用盘点 |
| 删除 `/api/c/self-service-api/` | 不再提供该历史路径的代理支持 |
| 删除 `_bk-esb-buffet-legacy-route` | 从 operator 的期望配置中移除，允许同步清理对应数据面路由 |
| 保留 `_bk-esb-compapi-legacy-route` | ID、匹配路径、重写目标和代理行为保持不变 |
| 主 Helm Chart 完整删除 ESB 逻辑 | 存量运行资源和入口由独立清单或独立 Chart 接管；主 Chart 仅保留通用扩展能力 |
| 删除 `bk-esb` 自动化注册及相关逻辑 | 不再自动创建网关、同步组件、同步密钥/白名单或自动发布 |
| 删除 EE ESB 管理接口 | EE 移除入口；TE 使用的公共实现和前端资产按第 1 节保留或迁移 |
| 认证路由选择去掉 `ENABLE_MULTI_TENANT_MODE` | 不再以多租户模式决定认证走网关还是 ESB；不改变其他租户行为或租户头语义 |

已确认：EE 登录认证走网关 `bk-login`，EE 通知走网关 `bk-cmsi`；TE 认证保持原有实现，通知继续走独立部署的内部 ESB，TE ESB 不下线。目标网关的实际接口可用性仍需在升级前验证。

## 3. 当前代码依据

本报告基于前序只读调查，版本基线如下。后续实施前应对目标发布分支复核。

| 仓库 | 调查基线 |
| --- | --- |
| blueking-apigateway | `bdd886ea74552416029376f4f8ca83f825e4056f` |
| helm-charts | 分支 `bk-apigateway-1.24.x`，提交 `0e04d876c9738f52f7f550cd94d714dcb5735a1e` |
| blueking-apigateway-apisix | 提交 `353a775e3e72671a209836f4559dd7c8eaca86e2`；本地存在其他未提交修改，不能作为线上镜像行为证明 |

主要证据入口：

- 网关初始化：[on_migrate](https://github.com/TencentBlueKing/blueking-apigateway/blob/bdd886ea74552416029376f4f8ca83f825e4056f/src/dashboard/bin/on_migrate)、[post_migrate](https://github.com/TencentBlueKing/blueking-apigateway/blob/bdd886ea74552416029376f4f8ca83f825e4056f/src/dashboard/bin/post_migrate)。目前 ESB 初始化主要由多租户模式判断控制。
- ESB 网关后端：[bk-esb-definition.yaml](https://github.com/TencentBlueKing/blueking-apigateway/blob/bdd886ea74552416029376f4f8ca83f825e4056f/src/dashboard/apigateway/apigateway/data/apigw-definitions/bk-esb-definition.yaml)。后端使用 `BK_COMPONENT_API_INNER_URL`。
- operator 额外资源加载：[virtual_stage.go](https://github.com/TencentBlueKing/blueking-apigateway/blob/bdd886ea74552416029376f4f8ca83f825e4056f/src/operator/pkg/core/synchronizer/virtual_stage.go)。额外路由归入虚拟环境管理。
- operator 差异更新：[store.go](https://github.com/TencentBlueKing/blueking-apigateway/blob/bdd886ea74552416029376f4f8ca83f825e4056f/src/operator/pkg/core/store/store.go)。期望配置缺失的旧路由可能进入删除集合。
- 登录配置：[default.py](https://github.com/TencentBlueKing/blueking-apigateway/blob/bdd886ea74552416029376f4f8ca83f825e4056f/src/dashboard/apigateway/apigateway/conf/default.py)。当前 EE 多租户分支使用 `bk-login`，其他分支仍存在 ESB 登录接口配置。
- 通知调用：[bkcmsi.py](https://github.com/TencentBlueKing/blueking-apigateway/blob/bdd886ea74552416029376f4f8ca83f825e4056f/src/dashboard/apigateway/apigateway/components/bkcmsi.py)。仍存在走 ESB 的通知实现和模式选择分支。
- ESB 数据模型：[bkcore/models.py](https://github.com/TencentBlueKing/blueking-apigateway/blob/bdd886ea74552416029376f4f8ca83f825e4056f/src/dashboard/apigateway/apigateway/editions/ee/apps/esb/bkcore/models.py)。包含组件、权限、配置、密钥等存量表定义。

跨仓库入口，以下路径相对于各自仓库根目录：

| 仓库 | 路径 | 关注点 |
| --- | --- | --- |
| helm-charts | `bk-apigateway/templates/operator/operator-configmap.yaml` | 两条历史 ESB 路由，当前绑定 ESB 渲染条件；通用 `operator.extraRoutes` |
| helm-charts | `bk-apigateway/templates/apigateway/apigateway-ingress.yaml` | ESB 与网关共用 Ingress，包含域名和子路径两种模式 |
| helm-charts | `bk-apigateway/templates/bk-esb/` | ESB 工作负载、服务、配置、证书、迁移和监控日志资源 |
| helm-charts | `bk-apigateway/templates/basic/init-sql-configmap.yaml` | 内置数据库初始化中的 ESB 建库及授权 |
| helm-charts | `bk-apigateway/templates/dashboard/` | ESB 数据库环境变量、证书挂载及等待 ESB 就绪逻辑 |
| blueking-apigateway-apisix | `src/apisix/plugins/bk-define/context-api-bkauth.lua` | ESB 类型对应的认证参数透传行为 |

## 4. Ingress 接管方案

### 4.1 结论

可以由 ESB 独立部署清单额外 apply 一个 Ingress。其后端继续指向原 APISIX Service，保留现有认证、权限和代理路径。

```text
调用方 /api/c/compapi/...
  → ESB 独立维护的 Ingress
  → 原 APISIX Service
  → _bk-esb-compapi-legacy-route
  → /api/bk-esb/prod/...
  → 存量 ESB Service
  → 组件后端
```

独立 Ingress 不直接指向 ESB Service，避免绕过现有网关认证和权限处理。

当前网关 Ingress 默认存在 `/` 兜底，删除 ESB 专用规则不一定立即断流。但自定义路径和子路径环境不能依赖这一点，应交付并验证明确的兼容入口。

### 4.2 配置约束

| 项目 | 要求 |
| --- | --- |
| 所有者 | ESB 独立清单或独立 Chart，不属于网关主 Chart |
| 对象名称 | 新名称，不直接修改网关主 Chart 管理的共享 Ingress |
| 域名 | 原调用域名不变 |
| IngressClass | 与现有入口一致 |
| 路径 | 只接管 `/api/c/compapi/`，不接管整个 `/api/c/` |
| 后端 | 原 APISIX Service 及实际 HTTP 服务端口 |
| Namespace | 与被引用的 APISIX Service 一致 |
| TLS 与注解 | 复用或补齐原入口必需的证书及配置，并明确维护归属 |
| 子路径模式 | 保留外部前缀匹配；转发到 APISIX 前还原为 `/api/c/compapi/...` |

对于 ingress-nginx，同 host 不同路径可以分布在多个 Ingress 中，由控制器合并。可先创建更具体的 compapi 路径，再升级移除旧 `/api/c/` 规则。应避免同 host、同 path 的重复规则，并按实际控制器和准入策略验证。[控制器行为说明](https://github.com/kubernetes/ingress-nginx/blob/main/docs/how-it-works.md)

子路径模式必须单独验证：同 host 任意 Ingress 使用 `rewrite-target` 或 `use-regex`，会影响该 host 下所有路径的匹配方式。[路径匹配说明](https://kubernetes.github.io/ingress-nginx/user-guide/ingress-path-matching/)

独立 Ingress 只解决入口，不解决 ESB Deployment、Service、配置和证书的保留问题。

## 5. 主 Chart 删除与存量资源保留

### 5.1 主 Chart 删除清单

- `templates/bk-esb/` 下 ESB 专用资源模板。
- `bkEsb` values、ESB 渲染 helper、ESB 数据库 helper 和相关配置。
- 数据库初始化 SQL 中 ESB 建库、授权逻辑。
- Dashboard 的 ESB 数据库环境变量、证书挂载和专用配置。
- Dashboard 迁移任务等待 ESB Job/Service 就绪的逻辑。
- 共享 Ingress 中 ESB 专用路径。
- operator 模板中的 ESB 专用条件及内置路由定义。
- ESB 自定义组件、外部依赖配置生成等辅助脚本和对应使用说明。

保留 `operator.extraRoutes`、额外卷等通用扩展能力，不因 ESB 删除而删除通用功能。

### 5.2 存量资源保留或接管

删除模板前，应完成以下资源清单的保留或独立接管：

- ESB Deployment、Service。
- 环境变量、运行配置、自定义组件 ConfigMap。
- 应用证书、数据库 TLS Secret 和其他实际挂载资源。
- ESB 所需数据库、账户及授权。
- 旧镜像及镜像拉取依赖，确保 Pod 重建仍能成功。
- 必需的日志、监控和运维配置。

Helm 对新版本中移除的资源可能执行删除。可以用 `helm.sh/resource-policy: keep` 作为过渡措施，但保留资源会脱离原 Chart 的管理，需要明确后续维护责任，并以实际 Helm 版本完成升级、失败恢复和回滚验证。[Helm 官方说明](https://v3-1-0.helm.sh/docs/howto/charts_tips_and_tricks/#tell-helm-not-to-uninstall-a-resource)

不能只更换资源 ownership 元数据就假定旧 release 不会删除资源；资源接管流程必须验证旧 release 的升级行为。不能通过给共享 Ingress 加 `keep` 来保证其中被删除的路径字段不变。

## 6. operator 与数据面兼容

### 6.1 compapi 路由

`_bk-esb-compapi-legacy-route` 保持原配置与行为，由存量部署配置通过通用 `operator.extraRoutes` 持续提供。

- 主 Chart 不内置 ESB 专用逻辑。
- 存量升级配置保留完整 compapi 路由，不改变 ID、重写目标、超时及代理语义。
- 全新部署不提供此路由。
- 迁移时避免内置和额外配置同时生成重复 ID；在准备阶段设计明确的切换顺序。

operator 会对虚拟环境执行差异同步，因此仅将旧路由留在 etcd 不足以保证兼容。必须在后续期望配置中持续存在。

### 6.2 buffet 路由

删除 `_bk-esb-buffet-legacy-route`，并检查存量通用额外路由配置中是否也有副本。不得在兼容清单中重新引入该路由。

验收时确认 `/api/c/self-service-api/` 不再通过专用路由进入 buffet；若环境存在自定义通配路由，应单独确认其实际匹配结果。

### 6.3 存量协议

保留已有 ESB 网关类型、认证参数透传规则和 JWT 语义。删除创建/同步命令，不意味着删除其已经产生并正在使用的协议支持。

验证范围包括 operator 重启、全局同步、普通网关发布，以及已有 `bk-esb` 配置重新发布后的行为。

## 7. Dashboard、数据与管理能力

### 7.1 EE 删除范围（公共实现先按第 1 节迁移 TE 依赖）

- `apps/esb/`、`editions/ee/apps/esb/`、`biz/esb/` 及专用辅助代码。
- Django app 注册、`bkcore` 数据库连接和 DB router 映射、ESB Celery imports/tasks。
- `on_migrate`、`post_migrate` 中 ESB 数据迁移、网关创建、组件同步、JWT/白名单同步、发布命令。
- ESB Web/Open/V2 Inner 管理接口、URL 注册、序列化器及接口定义和文档。
- ESB 组件管理、文档/SDK 页面、菜单、服务调用、类型及功能开关。
- 删除后失去生产消费者的 ESB 专用依赖、测试和配置；共享依赖须先确认其他消费者。

### 7.2 数据保留要求

不执行删库、删表、撤权、清空配置或自动清理已有 ESB 网关数据。

保留：

- ESB 库中的已有表、组件配置、权限、账户和密钥数据。
- 网关主库中已有 Gateway、Stage、Resource、Backend/BackendConfig。
- 已有 ResourceVersion、Release、权限和认证配置。
- 对应控制面与数据面 etcd 中继续运行所需的发布配置。
- ESB 与网关之间的 JWT 密钥对应关系。

卸载 Django 模型和 app 时，不生成会实际删除存量表的迁移。删除迁移代码前检查其他 app 的历史迁移依赖，保证新安装和升级都能完成迁移。

保留原 ESB Service DNS/端口；若独立接管导致地址变化，需要显式迁移存量后端配置，不能只调整入口 Ingress。

### 7.3 EE 管理下线后的边界

EE 存量调用继续支持，但不再提供 ESB 专用组件管理、同步发布、权限申请/续期、文档和 SDK 管理能力。接口下线须在 1.25 公告具体路径和调用方适配要求。

权限仍按原有效期执行。需要验证通过普通网关权限能力维护存量权限的方式；不通过取消权限校验或无限延长有效期实现兼容。

## 8. 认证与其他运行依赖

### 8.1 EE 认证（TE 保持原行为）

已确认按以下目标实施：

- Dashboard 登录认证统一走网关 `bk-login`。
- 删除使用 `ENABLE_MULTI_TENANT_MODE` 选择网关或 ESB 的分支。
- 删除对应 ESB 登录认证 URL 和调用逻辑。
- 保留租户模式在其他业务中的作用及既有租户头语义。
- 不顺带删除 `EDITION` 差异；TE 的认证覆盖单独核对。

当前 EE 网关认证路径为：

```text
bk-login/prod/login/api/v3/open/bk-tokens/userinfo/
```

需确认目标平台部署了兼容接口，并验证非多租户与多租户环境的实际登录行为。

### 8.2 EE 通知（TE 依赖单独保留）

已确认 EE 通知迁移到 `bk-cmsi` 网关，不再依赖 ESB；TE 通知继续使用独立部署的内部 ESB，保留现有接口、配置和调用行为。

删除 EE/TE 通知路由选择中的 `ENABLE_MULTI_TENANT_MODE` 条件，以版本选择实现。EE 使用 `BKCMSIGateway`，TE 保留 `CMSIComponent`。EE 告警仅选择已支持的微信通知，TE 保留 IM 和微信；避免不支持的 IM 调用阻断通知或使告警被错误标记为失败。保留 TE 所需 ESB SDK 和配置；实施时验证 `bk-cmsi` 接口协议及可用性，不改变租户头语义。

## 9. 版本安排与升级顺序

### 9.1 1.25

1. 在 CHANGELOG、README、NOTES 和 ESB 配置说明中公告 1.26 下线范围与不再兼容的 self-service 路径。
2. 盘点存量运行资源、外部依赖、入口模式、权限有效期及自定义配置。
3. 提供并验证 ESB 资源保留/接管流程，保证原 Service 和配置可用。
4. 提前部署独立 compapi Ingress，确认流量仍经过 APISIX。
5. 准备 compapi 路由转入通用额外配置的确定切换流程。
6. 明确认证、通知的目标网关依赖及升级前置条件。

### 9.2 1.26

1. 确认存量资源和独立 Ingress 接管准备已完成。
2. 使用包含 compapi 路由的存量升级配置执行升级。
3. 主 Chart 删除 ESB 专用模板、配置、入口及内置路由逻辑。
4. 删除 ESB 服务模块、自动注册和管理能力，移除 buffet 路由。
5. 执行存量流量、重启恢复和无 ESB 新安装验收。

不假定所有用户都经过 1.25。是否支持跳过 1.25 直接升级需要明确；若支持，必须提供等价的迁移准备步骤。未经准备直接升级不能宣称满足无损兼容。

## 10. 验收清单

| 场景 | 通过条件 |
| --- | --- |
| 全新非多租户安装 | 不产生 ESB 服务、数据库、网关、兼容 Ingress 和 compapi 兼容路由；迁移及启动成功 |
| 全新多租户安装 | 同样无 ESB，租户认证与隔离行为正常 |
| 存量升级 | ESB 数据和运行资源未被删除，原 Service 地址可用 |
| 旧 compapi URL | `/api/c/compapi/...` 经 APISIX 进入存量 ESB，响应及认证语义保持 |
| 网关 compapi URL | `/api/bk-esb/prod/...` 继续可用 |
| self-service 下线 | 专用路径不再进入 buffet，数据面无 buffet 兼容路由 |
| Ingress 模式 | 域名和子路径模式均验证；其他同 host 路径不受影响 |
| operator 重启/全局同步 | compapi 路由仍在，buffet 路由不被重新创建 |
| 网关重新发布 | 已有 ESB 后端、JWT、认证参数透传及权限行为保持 |
| ESB Pod 重建 | 镜像可拉取，配置和证书可挂载，流量恢复正常 |
| 权限 | 有权限、无权限、过期权限均按原契约处理；明确后续维护方式 |
| EE 管理接口下线 | EE 无残留调用，内置接口资源定义与文档一致；不影响 TE |
| TE 功能保持 | 权限申请、续期、记录查询、原审批链路、文档和 SDK 展示保持；接口不被升级撤销 |
| TE 构建与配置 | edition 合成后导入、app、DB router、模型、board 和认证配置正常；原表和数据不变 |
| 登录与通知 | 新安装无需 ESB 即可完成登录和通知；验证非多租户分支 |
| 升级失败与回滚 | 不误删接管资源，不发生资源所有权冲突或重复路由；以实际 Helm 版本验证 |

## 11. 待确认事项与证据限制

实施前需要明确：

1. EE `bk-login` 和 `bk-cmsi` 的部署版本、接口可用性与升级前置检查。登录及通知目标已确认，不再作为产品选择待定。
2. TE 独立 ESB 的通知回归验证及原配置保留。
3. 存量 ESB 采用独立 Chart 还是独立清单维护，以及后续维护责任。
4. 是否支持跳过 1.25 直接升级，以及对应迁移流程。
5. ESB 管理接口删除后，存量权限的维护和续期方式。

本报告提供源码与模板支持的方案，不代表已实现或已完成线上验证。尚未执行代码删除、Chart 渲染、数据库迁移、集群升级、流量测试或回滚测试。实际 Helm/Ingress 控制器版本、部署 values、自定义组件和资源清单需在实施阶段核实。

### TE 发布定义维护边界

TE overlay 保留完整的 `bk-apigateway-definition.yaml` 和 `bk-apigateway-resources.yaml`，确保原有 ESB 权限接口继续发布和授权。当前内容与公共定义的差异为 ESB paths 和 grants；后续公共 API 定义发生变化时，必须同步 TE 快照。现有 API 一致性检查不能覆盖所有 backend/authConfig 等元数据差异，这是 draft 的维护风险。
