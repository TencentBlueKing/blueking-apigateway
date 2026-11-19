# 资源认证：一套策略、两种入口、一套应用权限

日期：2026-11-17

状态：已实施，见 Dashboard [#3543](https://github.com/TencentBlueKing/blueking-apigateway/pull/3543)、APISIX [#208](https://github.com/TencentBlueKing/blueking-apigateway-apisix/pull/208)（draft）。已按 2026-11-17 方案评审、2026-11-18 两轮代码评审及其遗留项讨论的决策修订；决策汇总见[附录](#附录决策记录)。

读者：Dashboard 后端、APISIX 插件、Dashboard 前端开发者，以及 bkauth 对接方

前置调研：《SaaS 用户委托 Token 接入网关调研》（内部文档，不随本仓库提交）。本方案在其“方案二”基础上收敛，差异见 [3.4](#34-与调研方案的关系)。

## 1. 结论

**资源只维护一套认证策略，由新表单编辑；请求按认证头进入新旧两种认证入口，认证通过后进入同一套应用权限校验。**

```text
新表单 ──映射为旧字段──┐
                      ├─→ 一套资源认证配置（存储与写入字段仍是现有字段）
同步 / 导入（格式不变）─┘          │
                                  ↓
X-Bkapi-Authorization ─┐
                       ├─→ 身份认证 ──→ 共用的应用权限校验（AppResourcePermission）
Authorization: Bearer ─┘
```

- 新增能力：资源支持 bkauth 为普通蓝鲸应用签发的两类 OAuth2 token：
  - **用户委托 token**（delegated）：用户授权应用代其访问后，bkauth 签发给该应用的 token，同时带有应用和用户身份，用于用户认证且开启“OAuth 授权”的资源；
  - **应用 token**（app-only）：应用以自身身份获取的 token（`client_credentials` grant），不带用户，用于仅应用认证的资源。
- 两者统称 OAuth 应用通道（下称应用通道）。资源开启应用认证（A=1）时，路由注入 OAuth2 插件；接受哪一类 token 由资源是否要求用户决定。
- 资源不新增存储字段。`oauth2_app_delegated_enabled` 等价于“用户认证且 `app_verified_required=true`”，`app_verified_required` 继续保留。
- 接口上的 `auth_type`、`oauth2_app_delegated_enabled` 都是**只读推导字段**；Web、同步、导入的写入仍只使用旧字段，同步 yaml 格式不变。
- 只在已发布投影 `ReleasedResource` 上新增两列冗余字段：`oauth2_app_delegated_enabled`（U && A）和 `oauth2_app_only_enabled`（!U && A），供 bkauth 的 scope 接口按索引筛选。
- 新增网关级开关 `Gateway.oauth2_app_enabled`，默认开启，网关管理员可按网关关闭应用通道（见 [3.5](#35-网关级开关)）。它控制 Bearer 入口是否接受用户委托 token 和应用 token，不改变资源认证配置和旧入口行为。
- 兼容范围：兼容旧格式导入、旧认证头调用方式；**不冻结资源修改前的认证要求**。在表单里关闭“OAuth 授权”，旧认证头调用也随之不再要求应用身份、不再校验应用权限。
- 绑定了旧插件 `bk-access-token-source` 的资源（不区分 `source`）不开放新增应用通道，投影列、scope、lookup 同样不列出（7.2）。
- 新插件对已开启 personal/public 的存量路由**不完全等同 `master`**：即使未重新发布，也按 bkauth 规则分流 Bearer（7.3），已确认接受。
- MCP Server 不新增应用通道开关，也不受 MCP Server 所属网关的开关影响。MCP 用户态入口按推导接受用户委托 token，应用态入口接受应用 token，都不允许关闭；入口不校验资源权限，由 mcp-proxy 校验 MCP Server 应用权限；入口同时接受 `mcp:{name}` 和网关范围的 audience（见 [第 8 节](#8-mcp-边界)）。

## 2. 现状

### 2.1 存储

| 配置 | 存储位置 |
| --- | --- |
| `auth_verified_required`、`app_verified_required`、`resource_perm_required` | 资源认证 `Context`（`resource_auth`）的 JSON 配置 |
| `oauth2_public_client_enabled`、`oauth2_personal_client_enabled` | `Resource` 列；发布时合入快照里的认证配置（[resource_auth.py](../src/dashboard/apigateway/apigateway/service/contexts/resource_auth.py)） |
| `is_public`、`allow_apply_permission` | `Resource` 列 |
| 发布态 public/personal | `ReleasedResource` 冗余列及索引（迁移 `0056`） |

### 2.2 数据面认证链

资源开启 public 或 personal 时，[RouteConvertor](../src/dashboard/apigateway/apigateway/controller/convertor/route.py) 为路由注入四个 OAuth2 插件。请求依次经过：

| 插件 | 旧认证头 | Bearer |
| --- | --- | --- |
| `bk-oauth2-protected-resource` | 有旧头即走旧流程；两种头都没有时返回 401（仅用户认证且带登录态 cookie 例外） | 标记 OAuth2 流程 |
| `bk-auth-verify` / `bk-oauth2-verify` | 旧流程校验 app_code+secret、SSM access_token、JWT、登录态 | bkauth 自省；`app.verified` 恒为 true |
| `bk-oauth2-appcode-validate` | 跳过 | 只放行 `public`/`personal` |
| `bk-auth-validate` | 按 `verified_app_required`/`verified_user_required` 校验 | 同样执行 |
| `bk-permission` | 按 app_code 查权限，受 `resource_perm_required` 控制 | 同样执行 |

结论：

- 应用权限本来就按 app_code 校验、不区分入口，新入口直接复用，不需要新的权限表。
- `app_verified_required` 在 Bearer 入口上恒满足，实际只约束旧入口。
- 旧认证头里的 `access_token` 走 SSM 自省，与 bkauth OAuth2 token 是两套体系。bkauth 签发的 token 只能走 Bearer 入口。

## 3. 配置模型

### 3.1 新表单与存储的对应

新表单：认证类型单选（无需认证 / 用户认证 / 应用认证）；用户认证下可多选“个人令牌”“公开客户端”“OAuth 授权”，“OAuth 授权”下有“开启应用白名单”；应用认证下有“开启应用白名单”；“是否公开”下有“允许申请权限”。

| 认证类型 `auth_type` | 子选项 | `auth_verified_required` | `app_verified_required` | `resource_perm_required` | Bearer 入口接受 | 对应的旧配置 |
| --- | --- | --- | --- | --- | --- | --- |
| `user` | OAuth 授权开启 | true | true | 白名单开关 | 用户委托 token（必须带用户）＋勾选的 personal/public | 应用＋用户认证（旧默认值） |
| `user` | OAuth 授权关闭 | true | false | false | 只接受勾选的 personal/public | 仅用户认证 |
| `user` | 三项都不勾 | true | false | false | 不开放；只能用旧方式带用户身份调用 | 仅用户认证 |
| `app` | — | false | true | 白名单开关 | 应用 token（不接受用户委托 token） | 仅应用认证 |
| `none` | — | false | false | false | 不开放 | 不认证 |

“Bearer 入口接受用户委托 token / 应用 token”以网关开关开启为前提；网关关闭时，所有资源的 Bearer 入口都不接受这两类 token，表中其他列不变（3.5）。

表单在“应用认证”下增加提示：“支持旧版应用凭证和 Bearer 应用 token 调用。”不增加开关，由 A 推导。

`oauth2_personal_client_enabled`、`oauth2_public_client_enabled` 只能在 `auth_type=user` 时开启（与现有校验一致）。

### 3.2 层级约束

```text
应用认证（app_verified_required）
  └─ 校验应用权限（resource_perm_required）
       └─ 允许申请权限（allow_apply_permission）   ← 同时要求 is_public=true
```

```text
resource_perm_required = app_verified_required and 提交值
allow_apply_permission = is_public and resource_perm_required and 提交值
```

上层为 false 时，下层在保存时强制写为 false，不报错。现有导入解析已对 `app_verified_required=false` 强制 `resource_perm_required=false`（[parser.py](../src/dashboard/apigateway/apigateway/biz/openapi/parser.py) `_adapt_auth_config`），本方案把同样的规则延伸到 `allow_apply_permission`，并覆盖 Web 创建、Web 更新、资源批量更新、同步和导入。

- 下层被强制写为 false 后不记忆原值。例如关闭 `is_public` 再打开，`allow_apply_permission` 仍为 false，需要用户重新勾选。
- 存量不满足层级的数据不做迁移；在下一次 Web 编辑、批量更新或同步时归一化。运行时仍按存储值执行。
- 归一化的可见影响：存量数据首次编辑、同步或导入时，可能因归一化在预览、资源版本 diff 和导出中出现差异（例如 `P=1, A=0` 变为 `P=0`）。数据面以实际发布并加载的版本为准，未重新发布前仍按旧版本执行。
- 资源批量更新的审计在 `data_after` 中同时记录请求值 `allow_apply_permission` 和实际写入结果 `allow_apply_permission_result: {"true": [资源 ID], "false": [资源 ID]}`，仍为一条批量审计。

字段语义（D6 / D10 / I9）：

- 表单的“OAuth 授权”就是 `app_verified_required`，**同时决定旧入口是否要求应用身份**，不只影响 Bearer 入口。
- “应用白名单”就是 `resource_perm_required`。`P=0` 只跳过认证通过后的应用权限校验，不跳过应用认证本身。它与原有的“免用户认证应用白名单”（`verified_user_exempted_apps`，豁免用户认证）是两套独立配置。
- `P=1` 依赖 `A=1`；“允许申请权限”依赖资源公开、`A=1` 且 `P=1`。

### 3.3 推导规则

```text
auth_type                    = user  if auth_verified_required
                               app   if not auth_verified_required and app_verified_required
                               none  otherwise
oauth2_app_delegated_enabled = auth_verified_required and app_verified_required       # 资源侧，只读；用户委托 token
oauth2_app_only_enabled      = not auth_verified_required and app_verified_required   # 仅已发布投影；应用 token
support_app（数据面）         = Gateway.oauth2_app_enabled and app_verified_required
                               and not 资源绑定 bk-access-token-source   # 7.2
```

`support_app` 只表达“资源接受应用通道”。接受哪一类 token 由路由已有的 `verified_user_required`（即 U）决定：要求用户时只接受用户委托 token，不要求用户时只接受应用 token（4.2）。下发配置表达资源要求，而不是枚举 token 类型，将来扩展 token 类型时只需升级插件，不需要全量重新发布。

`skip_auth_verification` 是存量内部字段，不参与推导，也不在表单中展示。

### 3.4 与调研方案的关系

| 议题 | 调研文档 | 本方案 |
| --- | --- | --- |
| 用户委托 token 的入口开关 | 方案二：A=1、U=1 即接受；方案三：额外的 API 开关 | 资源级采用方案二：由 A、U 推导，没有独立开关；另设网关级开关，默认开启（3.5） |
| `resource_perm_required=false` 时用户委托 token 是否仍查权限 | 方案二、三都强制查权限 | **不强制**，由“应用白名单”开关控制，与旧入口一致 |
| 免用户认证名单、`skip_auth_verification` | 用户委托 token 必须带有效用户，不受豁免 | 相同 |
| 应用 token（`client_credentials`） | 本期拒绝 | **本期支持**，只用于仅应用认证（U=0、A=1）的资源；校验 audience；scope 新增 `app_only` 类型 |
| MCP | 需改 JWT 透传和 mcp-proxy | 用户态入口接受用户委托 token、应用态入口接受应用 token；入口不查资源权限，沿用 mcp-proxy 现有 MCP Server 权限校验，不改 JWT（第 8 节） |

### 3.5 网关级开关

| 项 | 约定 |
| --- | --- |
| 存储 | `Gateway` 表新增 `oauth2_app_enabled`（`default=True, db_default=True`） |
| 默认值 | 新建网关与存量网关都为开启 |
| 修改入口 | 网关管理员在网关基本信息页切换；v2 网关同步 API 支持该字段（5.3） |
| 数据面生效 | 重新发布后生效。发布时读取网关当前值，不进资源版本快照，与网关认证配置的读取方式一致 |
| scope / lookup | 立即按当前值过滤（5.5） |
| 作用范围 | 控制 Bearer 入口是否接受用户委托 token 和应用 token：关闭后用户认证与仅应用认证的资源都不再因应用通道注入插件；不改变资源认证配置，不影响旧认证头的应用认证和权限校验，不影响 personal/public |
| MCP | 不受影响（第 8 节） |

不放在网关认证配置 `api_auth` Context 中：Context 是存量兼容对象，不再扩展；且 `Context.config` 是序列化后的 JSON 文本，scope 接口无法在 SQL 中按开关过滤。

资源表单：网关关闭时，“OAuth 授权”照常展示并可编辑，因为它仍决定旧入口是否要求应用身份；同时提示“网关已关闭 OAuth 应用通道，Bearer 调用不可用；此开关仍控制旧版调用方式是否校验应用身份”。

命名区分：网关字段为 `Gateway.oauth2_app_enabled`（可写，覆盖用户委托 token 和应用 token）；资源字段为 `auth_config.oauth2_app_delegated_enabled`（只读推导，值为 U && A，不含网关开关）。实现时同步写入 [DDD 统一概念词汇](ddd-ubiquitous-language.md)。

## 4. 运行时行为

### 4.1 入口分流

入口识别由路由上的 `bk-oauth2-protected-resource` 完成，**只在注入了 OAuth2 插件的路由上生效**（注入条件见 7.2）。

**bkauth Bearer**：指 `Authorization: Bearer <token>` 且 token 带有 bkauth 的固定前缀。网关只拦截 bkauth Bearer；其他 Bearer（后端自有 token 等）不进入新认证链路，按普通请求头处理并原样透传给后端。前缀只用于判断“是否交给 bkauth 自省”，token 的身份、模式、应用仍以 bkauth 自省结果为准，不从 token 字符串推断（与调研文档 5.1 一致）。

已确认的两种前缀，在 APISIX 侧做成配置（见 7.1）：

| 前缀 | 形式 | 完整格式 |
| --- | --- | --- |
| `bk` + 类型码 + `_` | 4 个字符，类型码为 `o`/`p`/`r`/`s` 之一 | `bk[oprs]_[0-9A-Za-z]{36}` |
| `tai_pat_` | 固定字符串；bkauth 对接外部认证太湖签发，走同一个 bkauth 自省接口 | 前缀之后的格式未约定，不做本地格式校验 |

匹配规则：

1. **是否拦截按前缀判断**：token 以 `bk[oprs]_` 或 `tai_pat_` 开头，即视为 bkauth Bearer。
2. **格式不符直接拒绝**：前缀命中、但不符合已知的完整格式（如 `bk[oprs]_` 后不是 36 位字母数字）时，直接返回 401，不调用 bkauth 自省，也不回退旧流程。
3. **类型码不决定身份**：网关不按类型码区分 personal/public/app，仍以自省返回的 `bk_app_code`、用户委托模式为准。

按前缀而不是完整格式判断是否拦截，是为了让带 bkauth 前缀的残缺 token 得到明确的拒绝，而不是被当作后端自有 token 静默透传。

**已注入 OAuth2 插件的路由**（`support_public`、`support_personal`、`support_app` 至少一个为真，且数据面版本支持）：

```text
有 X-Bkapi-Authorization  → 旧流程（优先级不变）
只开启了应用通道且未配置 bearer_token_rules → 任何 Bearer 都交给旧流程（规则漏配兜底，见下）
有 bkauth Bearer          → OAuth2 流程；格式不符或自省失败直接拒绝，不回退 Cookie 或旧凭证
以上都没有                → 有符合条件的登录态 cookie（仅用户认证资源）：旧流程
（含非 bkauth Bearer、      路由开启了 personal/public：返回 401 和 WWW-Authenticate（现状，供 MCP 客户端发现授权入口）
  解析不出 token 的空 Bearer） 只开启了应用通道：交给旧流程（旧流程可读 query/body 参数和登录态 cookie）
```

- 非 bkauth Bearer 视同没有 OAuth2 凭证：不阻止登录态 cookie 分支，也不被网关删除。`Authorization: Bearer` 后面没有 token 时同样视同无凭证，可以继续尝试符合条件的 cookie。
- 规则配置路径为 `bk_gateway.bk_oauth2.bearer_token_rules`（7.1）。**未配置（nil）时**，为兼容旧行为，插件把所有可解析的 Bearer 都当作 bkauth Bearer；只开启应用通道的路由（`challenge_on_missing_credential=false`）此时不拦截任何 Bearer，交给旧流程继续执行资源要求的认证和权限校验，应用通道在规则下发前等同关闭。personal/public 路由仍拦截全部 Bearer（与改造前一致）。正常部署由 Helm 保证规则非空且有效，空列表 `[]` 视为“已配置但不拦截任何 Bearer”。
- 同一新版插件和规则下，显式下发 `challenge_on_missing_credential: true`、`support_app: false` 与省略这两个字段等价。
- 网关消费的 OAuth2 凭证（命中规则并完成校验的 Bearer）不传给后端。客户端应只携带一种网关认证凭证：请求进入旧入口，或路由未挂 OAuth2 插件时，未被消费的 Bearer 会原样透传后端。这是现有透传边界，本期不改；已确认没有业务依赖 bkauth Bearer 透传给后端。
- “只开启应用通道时交给旧流程”是必须的。旧的默认配置（应用＋用户认证）和仅应用认证的资源都会开启应用通道，如果沿用现在的 401，允许从请求参数取认证信息的网关上，把凭证放在 query/body 里的调用都会失败，缺少凭证时的错误码也会变化。仅应用认证的资源不能开启 personal/public，因此总是交给旧流程。
- 已注入插件的路由上，过期或无效的 bkauth Bearer 即使同时带有有效登录态 cookie 也会被拒绝。旧默认配置的资源注入插件后，这是相对改造前的行为变化，已确认接受。
- 仅应用认证的资源改造前不注入插件，Bearer 一律透传后端；改造后带 bkauth 前缀的 Bearer 会被网关拦截并按 4.2 校验，非 bkauth Bearer 仍透传。

存量资源重发后对 bkauth Bearer 的处理（D4 / D8）：

| 存量资源 | 改造前 | 重新发布后 |
| --- | --- | --- |
| 应用＋用户认证（旧默认值），未开 personal/public | 不注入插件，Bearer 透传后端 | 注入插件；bkauth Bearer 被网关消费并按用户委托 token 校验，不再透传；非 bkauth Bearer 透传 |
| 仅应用认证 | 不注入插件，Bearer 透传后端 | 注入插件；bkauth Bearer 被网关消费并按应用 token 校验，不再透传；非 bkauth Bearer 透传 |
| 上述两类且绑定 `bk-access-token-source` | 由该插件读取 Bearer 或 `X-API-KEY` | 不开放应用通道（7.2），行为不变 |

**未注入 OAuth2 插件的路由**（三者都为假，例如 `auth_type` 为 `none`、用户认证下三项全关，或网关关闭开关且资源未开启 personal/public）：

- 网关不识别、不拦截 Bearer，只有旧认证链路。`Authorization` 头按普通请求头处理，原样透传给后端（`bk-delete-sensitive` 只删除 `X-Bkapi-Authorization`）。
- 认证结果完全由旧链路决定。例如“仅用户认证”的资源收到过期 Bearer 和有效登录态 cookie，会按 cookie 认证通过，Bearer 透传给后端。
- 这是有意的：与改造前所有未开启 OAuth2 的资源行为一致，也不影响后端自有的 `Authorization` 协议。“bkauth token 无效直接拒绝、不回退”只针对已注入插件的路由。

因为只拦截 bkauth Bearer，旧默认配置的资源大量注入插件后，后端自有的 Bearer 协议不受影响：调用方把应用凭证放在 query/body 中、同时携带后端自有 Bearer 时，仍走旧流程，Bearer 透传后端。

与现状的差异：当前插件对任何 Bearer 都进入 OAuth2 流程，开启了 personal/public 的路由收到非 bkauth Bearer 时会拒绝。改造后这类请求按“无 OAuth2 凭证”处理：有符合条件的 cookie 时走 cookie 认证并保留后端自有 Bearer，没有可用旧凭证时仍返回 401 和 WWW-Authenticate。这属于放宽，不影响已有的 bkauth token 调用——bkauth 已确认存量 personal/public token 都符合当前规则（见第 11 节）。这项变化由新插件带来，存量 personal/public 路由在**只升级 APISIX、尚未重新发布**时也会发生；网关关闭应用通道（`oauth2_app_enabled=false`）也只关闭真实应用 token，不恢复旧的“所有 Bearer 进 OAuth2”分流（PR-1，已确认接受）。

### 4.2 Bearer 入口的用户委托 token 与应用 token 校验

放行需要满足以下条件：

1. bkauth 自省有效、未过期、必需字段完整。
2. 按 bkauth 自省字段判定 token 模式：`sub`、`client_id` 和原始 `username` 都是非空字符串时为用户委托 token，允许 `sub == client_id`。仅当 `sub`、`client_id` 是相同的非空字符串，且 `username` 为原始空字符串 `""` 时，判为应用 token。其他组合为 `unknown`。当前 `bkauth.lua` 把 `sub` 映射为 `bk_username`，应用 token 的 `sub` 同样非空，所以不能再用“`bk_username` 非空”判断是否带用户，需要保留原始 `username`、`client_id`。
3. `bk_app_code` 是真实应用（不是 `public`/`personal`/空），且路由 `support_app=true`（已包含网关开关）。
4. token 模式与资源要求匹配：
   - 资源要求用户（`verified_user_required=true`）：只接受用户委托 token，且必须有有效用户，不受免用户认证名单和 `skip_auth_verification` 影响；应用 token 拒绝。
   - 资源不要求用户（仅应用认证）：只接受应用 token；用户委托 token 拒绝。
5. audience 覆盖当前资源（`gateway:{网关}/api:{资源}` 或通配）。应用 token 同样校验。MCP 入口另外接受 `mcp:{name}` / `mcp:*`（第 8 节）。
6. `resource_perm_required=true` 时，按真实 app_code 查网关级/资源级权限（与旧入口同一份数据）。

- 模式判定的边界：`sub` 或 `client_id` 缺失、为空或不是字符串，或者 `username` 缺失、为 JSON `null` 或其他非字符串时，模式归为 `unknown`。职责划分为：`bk-oauth2-verify` 获取自省结果、识别模式并写上下文 `bk_oauth2_token_mode`；`bk-oauth2-appcode-validate` 拒绝真实应用的 `unknown`。`unknown` 的拒绝**只针对真实应用**，personal/public 沿用现有校验，不看 token 模式（bkauth 已确认 personal/public token 不会同时满足 `sub == client_id` 且 `username` 为空）。
- 应用身份以自省返回的 `bk_app_code` 为准；`client_id` 只参与模式判定，两者各自保留原语义。
- 失败响应：
  - token 模式与资源要求不匹配（两个方向）、真实应用的 `unknown`、应用码不被允许：`401` ＋ `WWW-Authenticate: Bearer ... error="invalid_token"`，`error_description` 和响应体的 `reason` 写明原因，例如 “the resource requires a user, only OAuth2 delegated tokens are allowed: bk_app_code=..., token_mode=app”。`bk-auth-validate`（优先级 17680）先于 `bk-oauth2-appcode-validate`（17678）执行，因此通用用户校验失败时由前者返回错误。应用通道同时关闭时，也按插件执行顺序返回先遇到的错误。
  - audience 不匹配：仍为 `403`（`invalid_audience`）。
  - 旧认证链路、personal/public 缺少用户：保持原有 `400`/`500`，不改。
- 应用 token 不带用户：`bk-oauth2-verify` 不得把 `sub`（等于 `client_id`）当作用户名写入上下文，后端收到的网关 JWT 中用户为空且未认证，与旧入口只带应用凭证的调用一致。
- `bk[oprs]_` 与 `tai_pat_` 两类 token 走同一条校验链，网关不按前缀区别对待。
- 多租户：沿用现有多租户插件，按自省得到的 `bk_app_code` 校验应用租户，不新增逻辑。
- AI 资源（`kind=ai`）与标准资源适用同一套规则。
- 后端收到的网关 JWT 不区分用户委托 token 调用与旧认证头调用。

personal、public 的现有校验和内置权限协调（[oauth2_builtin.py](../src/dashboard/apigateway/apigateway/controller/tasks/oauth2_builtin.py)）不变。

### 4.3 旧认证头

不做任何改动。旧入口按推导后的 `auth_verified_required`、`app_verified_required`、`resource_perm_required` 执行。SSM `access_token` 继续可用，将随 SSM 下线逐步退场，调用方迁移到 bkauth＋Bearer 不在本期范围。

### 4.4 需要在前端交接中写清楚的行为变化

| 操作 | 旧认证头调用 | Bearer 调用 |
| --- | --- | --- |
| 用户认证下关闭“OAuth 授权” | 不再要求应用身份，不再校验应用权限，申请入口关闭；仍需用户身份 | 拒绝用户委托 token；personal/public 按各自开关 |
| 关闭“应用白名单” | 任意应用（有合法凭证）可调用 | 任意应用的用户委托 token（带用户、aud 匹配）可调用 |
| 应用认证 → 用户认证（OAuth 授权开启） | 新增“必须带用户”的要求 | 从接受应用 token 改为接受用户委托 token |
| 用户认证（OAuth 授权开启）→ 应用认证 | 不再要求用户身份 | 从接受用户委托 token 改为接受应用 token；personal/public 随用户认证关闭 |
| 用户认证下三项全部关闭 | 只校验用户身份 | 网关不识别 Bearer，`Authorization` 头透传后端 |
| 网关关闭 OAuth 应用通道并重新发布 | 不变 | 拒绝用户委托 token 和应用 token；personal/public 不受影响 |
| 关闭“是否公开” | 不变；“允许申请权限”自动关闭 | 不变 |

建议的表单提示文案：

- 关闭 OAuth 授权：“关闭后，旧版调用方式也将不再校验应用身份和应用权限，只校验用户身份。”
- 开启 OAuth 授权：“开启后，所有拥有本资源权限的蓝鲸应用，都可以在用户授权后以该用户身份调用。”
- 应用认证：“支持旧版应用凭证和 Bearer 应用 token 调用。”
- 网关已关闭 OAuth 应用通道：“网关已关闭 OAuth 应用通道，Bearer 调用不可用；此开关仍控制旧版调用方式是否校验应用身份。”
- 网关基本信息页切换开关：“修改后需要重新发布各环境才在数据面生效。”
- 配置修改需要发布后才在数据面生效。

## 5. 接口契约

### 5.1 Web 接口：读取

资源列表、详情、版本详情中的 `auth_config` 新增两个只读推导字段，原有字段原样返回：

```json
{
  "auth_type": "user",
  "oauth2_app_delegated_enabled": true,
  "oauth2_personal_client_enabled": false,
  "oauth2_public_client_enabled": false,
  "auth_verified_required": true,
  "app_verified_required": true,
  "resource_perm_required": true
}
```

- 资源侧 `oauth2_app_delegated_enabled` 值为 U && A，不含网关开关；前端结合网关详情中的开关展示提示（3.5）。
- `allow_apply_permission`、`is_public` 仍在资源顶层。
- 网关详情新增 `oauth2_app_enabled`。

### 5.2 写入：归一化规则（Web 与同步共用）

写入只使用旧字段。`auth_type`、`oauth2_app_delegated_enabled` 是只读字段，Web 和同步写入时忽略，不影响存储。因此不存在新旧字段冲突。

字段对应（Web 用 snake_case，同步用 camelCase）：

| 维度 | 写入字段 |
| --- | --- |
| 用户认证 U | `auth_verified_required` / `userVerifiedRequired` |
| 应用认证 A | `app_verified_required` / `appVerifiedRequired` |
| 应用权限 P | `resource_perm_required` / `resourcePermissionRequired` |
| 允许申请 | `allow_apply_permission` / `allowApplyPermission` |
| 是否公开 | `is_public` / `isPublic` |
| personal/public | `oauth2_personal_client_enabled`、`oauth2_public_client_enabled` / 对应 camelCase |

归一化顺序：

1. **确定各维度取值**：显式提交的值优先；未传时按入口取缺省值（见下表）。Web 更新需要区分“未传”和“传 false”。
2. **校验约束**：U=false 而 personal 或 public 为 true → 400（现状）。
3. **按层级确定 P 与允许申请**（3.2）：上层关闭时下层写为 false，不报错。
4. 写入 `auth_verified_required`、`app_verified_required`、`resource_perm_required`、`allow_apply_permission` 和两个 OAuth2 列。

缺省值按入口区分：

| 入口 | U、A、P、允许申请未传 | personal/public 未传 |
| --- | --- | --- |
| 同步 API、资源导入（声明式） | true（旧默认值） | false |
| Web 创建 | true | false |
| Web 更新 | 保留当前存储值 | 保留当前存储值（现状） |

Web 更新“保留当前存储值”同时修复一个存量问题：现在省略 `app_verified_required`、`resource_perm_required` 时会被 Pydantic 默认值写成 true（[biz/resource/models.py](../src/dashboard/apigateway/apigateway/biz/resource/models.py)、[savers.py](../src/dashboard/apigateway/apigateway/biz/resource/savers.py) `_save_auth_configs`）。

资源批量更新（`ResourceBatchUpdateInputSLZ`）同时提交 `is_public`、`allow_apply_permission`：对每个资源按提交的 `is_public` 和该资源当前的 `resource_perm_required` 归一化 `allow_apply_permission`，不满足时静默写 false。

新表单提交约定（前端）：表单把界面选项映射为旧字段，总是提交全部字段，不依赖缺省值。

| 表单选择 | `auth_verified_required` | `app_verified_required` | `resource_perm_required` |
| --- | --- | --- | --- |
| 无需认证 | false | false | false |
| 应用认证 | false | true | 白名单开关 |
| 用户认证，OAuth 授权开启 | true | true | 白名单开关 |
| 用户认证，OAuth 授权关闭 | true | false | false |

- `oauth2_personal_client_enabled`、`oauth2_public_client_enabled`：非用户认证时提交 false。
- `is_public`、`allow_apply_permission`：总是提交；上层关闭时后端写为 false。
- 新建资源的表单默认值：用户认证＋OAuth 授权开启＋白名单开启，与后端缺省值一致。

### 5.3 同步 API 与资源导入

资源同步与导入：

- `x-bk-apigateway-resource.authConfig` **格式不变，不新增字段**；[openapi_2.0/3.0/3.1 schema](../src/dashboard/apigateway/apigateway/biz/openapi/schemas/) 不改。
- 只带旧字段的存量 yaml 行为不变；省略时仍按旧默认值 true 处理，即“用户认证＋OAuth 授权开启＋白名单开启”。
- 同步仍是声明式的；省略 `oauth2PublicClientEnabled`/`oauth2PersonalClientEnabled` 仍按 false 处理（现状）。
- `_adapt_auth_config` 的层级处理延伸到 `allowApplyPermission`（同时要求 `isPublic`），按 5.2 执行。

网关同步（[v2 sync](../src/dashboard/apigateway/apigateway/apis/v2/sync/serializers.py) `GatewaySyncInputSLZ`）：

- 新增可选字段 `oauth2_app_enabled`（boolean）。
- 未传时：新建网关为 true；已有网关保留当前值，避免同步把管理员在页面上关闭的开关重新打开。
- 旧版 open 同步接口（`apis/open/gateway`）不新增该字段。

### 5.4 导出

**导出格式不变，只输出旧字段。** 资源侧新字段可以完全从旧字段推导，不携带也不丢信息；而旧版本网关的导入 schema 会拒绝不认识的 `authConfig` 字段，加入新字段反而会导致导出文件无法导入未升级的环境。网关开关属于网关配置，不进入资源导出。

### 5.5 bkauth scope 与 lookup 接口

`GET /api/v2/inner/oauth2/client-scopes/resources/`（[OAuth2ResourceScopeListApi](../src/dashboard/apigateway/apigateway/apis/v2/inner/views.py)）的 `oauth_client_type` 新增 `app_delegated` 和 `app_only`：

```text
oauth_client_type=app_delegated → 当前生效版本中 is_public=true 且 oauth2_app_delegated_enabled=true（U && A）的资源，
                                  且所属网关 Gateway.oauth2_app_enabled=true，按网关分页
oauth_client_type=app_only      → 当前生效版本中 is_public=true 且 oauth2_app_only_enabled=true（!U && A）的资源，
                                  且所属网关 Gateway.oauth2_app_enabled=true，按网关分页
```

- `app_delegated` 供用户授权页为用户委托 token 选择 scope；`app_only` 供应用为应用 token 选择 scope。
- scope 取各环境当前发布版本的**并集**：同一资源在一个环境发布为用户委托（U=1）、在另一个环境发布为仅应用（U=0）时，两种类型下都会列出。lookup 读取单个版本，只显示该版本的模式。调用能否成功由目标环境的路由决定，scope 和 lookup 不代表某个环境一定可调用。同一环境的同一版本中，一个资源只会属于其中一种类型。
- 绑定 `bk-access-token-source` 的资源，投影两列都为 false，scope、lookup 不列出，与路由不开放应用通道一致（7.2）。
- 命名约定：`app_` 前缀表示真实蓝鲸应用作为客户端（区别于 `public`/`personal`），后缀表示是否带用户；不按 OAuth2 grant 类型命名，因为 public 客户端同样走授权码流程并带用户，按 grant 命名会与之冲突。
- `ReleasedResource` 每个资源版本只写一次（`save_released_resource` 在已存在且非 `force` 时直接返回），并由发布该版本的所有环境共用，所以新列只能存资源快照的推导值（U、A 与是否绑定 `bk-access-token-source`），不能写入网关开关。网关开关在 scope 查询时按当前值过滤。
- 因此网关开关在 scope 上立即生效，在数据面上要等重新发布：关闭后、重新发布前，scope 不再列出但数据面仍接受；开启后、重新发布前，scope 已列出但数据面仍拒绝。

MCP scope 接口 `GET /api/v2/inner/oauth2/client-scopes/mcp-servers/`（[OAuth2MCPServerScopeListApi](../src/dashboard/apigateway/apigateway/apis/v2/inner/views.py)）同样新增 `oauth_client_type=app_delegated`：

```text
oauth_client_type=app_delegated → 所有满足现有可见条件的 MCP Server（网关启用且公开、环境启用、Server 启用且公开），不按开关筛选
```

- MCP Server 没有应用通道开关，用户态入口默认接受用户委托 token 且不允许关闭，也不受 MCP Server 所属网关的开关影响，所以 `app_delegated` 的候选集合就是全部可见 MCP Server。`_get_oauth2_mcp_servers` 对 `app_delegated` 不加开关字段条件。
- MCP scope **不新增** `app_only`。MCP 入口同时接受 `mcp:{name}` / `mcp:*` 和网关范围 audience（`gateway:*`、`gateway:bk-apigateway/api:*` 等），应用 token 可经资源 scope 获得后者；bkauth 签发约定见第 8 节、第 11 节。
- 资源与 MCP 两个接口的可选类型不再相同：资源接受 `public`/`personal`/`app_delegated`/`app_only`，MCP 接受 `public`/`personal`/`app_delegated`。拆分现有共用的 `OAUTH2_CLIENT_TYPES`；`OAUTH2_CLIENT_TYPE_FIELD_MAP` 只给资源用，资源侧 `app_delegated`、`app_only` 额外关联网关开关，MCP 侧对 `app_delegated` 单独处理。

非公开对象：scope 列表只列公开的网关、资源和 MCP Server（与 personal/public 一致）。非公开的网关、资源或 MCP Server 由用户在授权页手填，bkauth 用现有 lookup 接口校验是否存在；这些接口本来就返回非公开对象。

lookup / list 接口输出：

| 接口 | 改动 |
| --- | --- |
| `GatewayReleasedResourceLookupApi`、已发布资源列表（共用 `GatewayReleasedResourceOutputSLZ` 与 `RELEASED_RESOURCE_FIELDS`） | 新增 `oauth2_app_delegated_enabled`、`oauth2_app_only_enabled`，值为对应 `ReleasedResource` 新列 && 网关开关当前值，与 scope 口径一致 |
| `MCPServerLookupApi`、MCP Server 列表 | 不新增字段；bkauth 约定用户委托 token 对 MCP Server 始终可用 |

同步更新 [v2_inner_list_oauth2_resource_scopes.md](../src/dashboard/apigateway/apigateway/data/apidocs/zh/v2_inner_list_oauth2_resource_scopes.md)、[v2_inner_list_oauth2_mcp_server_scopes.md](../src/dashboard/apigateway/apigateway/data/apidocs/zh/v2_inner_list_oauth2_mcp_server_scopes.md)、[v2_inner_lookup_gateway_released_resources.md](../src/dashboard/apigateway/apigateway/data/apidocs/zh/v2_inner_lookup_gateway_released_resources.md)、[v2_inner_list_gateway_released_resources.md](../src/dashboard/apigateway/apigateway/data/apidocs/zh/v2_inner_list_gateway_released_resources.md)。

需要提前告知 bkauth：

1. `app_delegated` 的 scope 远大于 public/personal。旧默认配置就是“开启 OAuth 授权”，网关开关又默认开启，回填后几乎所有公开网关的公开资源、全部可见 MCP Server 都会出现在 `app_delegated` 的列表里，授权页面需要分页和按网关检索。`app_only` 同样会包含所有公开的仅应用认证资源。
2. scope 可选不等于一定能调通：
   - 迁移回填后 scope 立即可见，但路由要等网关下一次发布才挂上应用通道，在此之前 Bearer 调用会被拒绝；
   - 网关开关切换后，scope 立即变化，数据面要等重新发布；
   - 应用没有资源权限（白名单开启时）或 MCP Server 权限时会被拒绝；scope 不按应用权限过滤；
   - scope 是各环境的并集，同一资源可能同时出现在 `app_delegated` 和 `app_only` 下，实际按目标环境的路由判定。
3. 非公开对象走手填＋lookup 校验；资源 lookup 新增 `oauth2_app_delegated_enabled`、`oauth2_app_only_enabled`，MCP lookup 不新增字段。
4. 网关接受普通蓝鲸应用的应用 token（`client_credentials` grant），只用于仅应用认证的资源，并校验 audience；用户委托 token 调用这类资源会被拒绝。
5. scope 类型取值为 `app_delegated`、`app_only`（资源）和 `app_delegated`（MCP），需与 bkauth 对齐。
6. MCP 入口接受网关范围 audience（第 8 节）：签发 `gateway:*` 或 `gateway:bk-apigateway/api:*` 的 token 可调用所有 MCP 入口，是否能访问某个 MCP Server 由 mcp-proxy 的 MCP Server 权限决定。

### 5.6 开发者中心可申请资源列表

开发者中心用 v2 inner 资源列表（[GatewayPermissionResourceListApi](../src/dashboard/apigateway/apigateway/apis/v2/inner/views.py)）展示和检索接口，不只是“可申请”列表。已发布的公开资源按下表返回：

| 资源 | 是否返回 | `permission_level` |
| --- | --- | --- |
| `P=1`，`A=1` 且 `allow_apply_permission=true` | 返回 | 沿用现有取值（`normal` 等） |
| `P=1`，但 `A=0` 或 `allow_apply_permission=false` | 不返回 | — |
| `P=0`（仅用户认证、应用态但不校验应用权限、无需认证） | 返回，即使 `allow_apply_permission=false` | `unlimited`，表示无需申请权限；调用时仍须满足资源的认证要求 |

- `P=1` 一行兼容 3.2 落地前不满足层级约束的存量数据。响应结构不变，同步更新 [v2_inner_list_gateway_permission_resources.md](../src/dashboard/apigateway/apigateway/data/apidocs/zh/v2_inner_list_gateway_permission_resources.md)。
- v1 资源列表（`apis/open/permission`）PaaS 已不再依赖，保留按 `allow_apply_permission` 筛选，在接口注释中说明与 v2 的差异：存量 `P=0` 资源经归一化（`allow_apply_permission` 写为 false）并重新发布后，可能从 v1 列表退出。

## 6. 存储与迁移

| 对象 | 改动 |
| --- | --- |
| `Resource` | 无新列 |
| 资源认证 `Context` | 无新字段；保存时执行层级约束 |
| `Gateway` | 新增 `oauth2_app_enabled`（`default=True, db_default=True`） |
| `ReleasedResource` | 新增 `oauth2_app_delegated_enabled`（U && A）和 `oauth2_app_only_enabled`（!U && A），都为 `default=False, db_default=False`，不含网关开关；各自建索引 `(<列>, is_public, gateway, resource_version_id, resource_id)`，与 public/personal 的索引同结构 |

迁移：

- `Gateway` 新列依靠数据库默认值把存量网关置为开启，不需要回填。
- `ReleasedResource` 两个新列由迁移 `0059_oauth2_app_access_fields` 回填：非原子，按主键 keyset 分页（`id > last_id ORDER BY id LIMIT 1000`，只取 `id`、`data`），避免 MySQL 客户端缓冲全量快照 JSON；从 `data.contexts.resource_auth.config` 推导 `auth_verified_required and app_verified_required`、`not auth_verified_required and app_verified_required`；快照 `data.plugins` 绑定 `bk-access-token-source` 时两者都为 false（7.2）；两者都为 false 的行不写。
- `0059` 的三个加列和两个索引使用普通的 `AddField`/`AddIndex`；迁移非原子只为让回填按批提交。上线前用接近生产的数据量演练索引构建耗时和锁等待（7.5）。
- 发布写入、`0059` 回填、`sync_released_resource --oauth2-app-flags` 补算都调用 `get_released_resource_oauth2_app_flags`，推导结果一致。
- 不修改任何存量认证配置，不做 `Resource` 层面的数据迁移。
- 两个新列都必须带数据库级默认值。0056 的列只有 Django 侧 `default=False`，数据库列是 NOT NULL 且无默认值；如果新列也这样，回滚到旧 Dashboard 后，旧代码创建 `Gateway`、写 `ReleasedResource` 时不带该列，会因为 NOT NULL 写入失败，导致创建网关或发布失败。有了数据库默认值，回滚 Dashboard 时可以不执行反向迁移，新列保留即可。
- 保留 `0059` 回滚的副作用：旧 Dashboard 在回滚期间首次发布新版本时，新建投影的两个新列取数据库默认值 false；再次升级不会重跑已完成的迁移，普通重发看到已有投影也会跳过。因此再次升级后必须补算，并重发回滚期间由旧 Dashboard 下发过的网关（7.4 第 7 步）：

```bash
# 从每个当前生效版本的资源快照重新推导两个新列，只更新不一致的行；缺投影的版本补建。可重复执行，不删除投影
python manage.py sync_released_resource --all --oauth2-app-flags --dry-run   # 先看会改多少行
python manage.py sync_released_resource --all --oauth2-app-flags
```

  不用 `--force`：它先删除再重建投影，期间 scope、lookup 会读到空结果，也会与正常发布竞争。

## 7. 数据面与发布

### 7.1 插件改动（blueking-apigateway-apisix）

| 插件 | 改动 |
| --- | --- |
| `bk-components/bkauth.lua` | 保留 `sub`（`bk_username`）、`client_id` 及原始 `username`（`bk_login_name`）。显式空字符串与缺字段分别处理 |
| `bk-oauth2-verify` | 按 4.2 识别用户委托/应用/`unknown` 模式并写入 `bk_oauth2_token_mode`；应用 token 不设置用户；删除已消费的 `Authorization`，避免透传后端 |
| `bk-oauth2-appcode-validate` | 新增 `support_app`（默认 false）：真实 app_code；按路由 `verified_user_required` 决定接受的模式——要求用户时只接受用户委托 token 且有有效用户，不要求用户时只接受应用 token；`unknown` 拒绝；失败 401（4.2） |
| `bk-auth-validate` | 真实应用的 OAuth2 token 忽略免用户认证名单和 `skip_user_verification`；要求用户的资源缺少有效用户时返回 401 ＋ `WWW-Authenticate`，与 appcode-validate 同一文案；旧链路和 personal/public 保持 400/500 |
| `bk-oauth2-protected-resource` | 只把命中规则的 Bearer 识别为 OAuth2 凭证，其他 Bearer 视同无 OAuth2 凭证；新增 `challenge_on_missing_credential`（默认 true），区分“缺少凭证时返回 401”和“交给旧流程”；规则缺失且为 false 时不拦截 Bearer（4.1）；新增 `init()` 加载时校验规则 |
| `bk-permission` | 不改，继续受 `resource_perm_required` 控制 |
| `bk-core` | `config.get_oauth2_bearer_token_rules`、`oauth2.classify_bearer_token`、`oauth2.get_user_required_token_reject_reason`、`oauth2.validate_bkauth_bearer_token_rules` |

部署配置路径为 `bk_gateway.bk_oauth2.bearer_token_rules`，由 Helm 下发，不在代码中硬编码：

```yaml
bk_gateway:
  bk_oauth2:
    bearer_token_rules:
      - prefix_pattern: "^bk[oprs]_"
        format_pattern: "^bk[oprs]_[0-9A-Za-z]{36}$"
      - prefix_pattern: "^tai_pat_"
```

- 按顺序匹配，第一条 `prefix_pattern` 命中的规则决定结果；`format_pattern` 存在时用于本地格式校验，不存在时直接交给 bkauth 自省。
- 请求侧使用加载后保存的规则，调用 `ngx.re.find` 执行匹配。非法 `prefix_pattern` 在加载时记录 error 并跳过该规则。提供的 `format_pattern` 必须是可编译的字符串，否则加载时记录 error，命中该前缀的 token 按格式不符返回 401。
- 规则缺失（nil）时的行为见 4.1。规则不是列表（布尔、字符串、数字、对象）时，请求阶段按未配置处理，与 nil 相同。部署验收需确认规则非空、有效，并覆盖存量 personal/public token 和后端自有 Bearer（7.5）。
- 加载时校验：`bk-oauth2-protected-resource.init()` 一次读取规则，检查列表、规则对象和正则，并保存处理结果。缺配置记一条 warn，非列表和空列表各记一条 error。规则项的配置错误在加载时记录，插件继续启动。

### 7.2 Dashboard 下发

```python
support_public = U and oauth2_public_client_enabled
support_personal = U and oauth2_personal_client_enabled
support_app = gateway.oauth2_app_enabled and A and not binds_access_token_source
inject = (support_public or support_personal or support_app) and apisix_version >= 3.16
challenge_on_missing_credential = support_public or support_personal
```

`binds_access_token_source`：按**本次发布的资源版本**快照中资源的 `plugins` 绑定判断，资源绑定了 `bk-access-token-source` 即为真，不区分 `source` 和 `allow_fallback`。该插件（优先级 18735）先于 `bk-oauth2-verify`（18732）执行：`source=bearer` 时它把 `Authorization: Bearer` 转换为旧凭证，与新增应用通道争用同一个头；`source=api_key` 且 `allow_fallback=false` 时，只带 Bearer 的请求缺少 `X-API-KEY`，被它直接返回 400。该插件已不公开、使用方为个位数，不再按配置细分，绑定即只关闭新增应用通道：

| 资源绑定情况 | 新应用通道 | 四个 OAuth2 插件 |
| --- | --- | --- |
| 绑定（任意 `source`、`allow_fallback`），未开启 personal/public | 关闭 | 不下发 |
| 绑定（任意 `source`、`allow_fallback`），已开启 personal/public | `support_app=false` | 按 personal/public 原有条件下发 |
| 未绑定 | 按网关开关、A 和数据面版本判断 | 按原有注入逻辑 |

- 标准资源和 AI 资源同一条件；APISIX 插件优先级不变。
- 资源表单仍可勾选“OAuth 授权”。屏蔽同时作用于路由下发和 `ReleasedResource` 投影：`core.managers.released_resource_binds_access_token_source` 按资源快照的 `plugins` 做同一判断，两列都为 false，scope、lookup 不列出。Web 只读的 `auth_config.oauth2_app_delegated_enabled` 仍按 U && A 推导，不受影响。
- 只有一处推导：controller 的 `support_app` 直接复用 `core.managers.get_released_resource_oauth2_app_flags`（A && 未绑定），与投影列一致；`core` 不能依赖 `apps`，插件类型常量 `core.constants.BK_ACCESS_TOKEN_SOURCE_PLUGIN_TYPE` 由单测锁定与 `PluginTypeCodeEnum` 一致。

- `support_app` 覆盖用户认证（U=1）与仅应用认证（U=0）两种资源；插件结合 `bk-resource-context` 中已有的 `verified_user_required` 决定接受用户委托 token 还是应用 token，Dashboard 不下发 token 类型。
- 网关开关由 `ReleaseData.gateway` 读取当前值，不来自资源版本快照。
- `RouteConvertor` 已按数据面持有 `apisix_version`，按数据面决定是否注入。标准路由与 AI 路由（`_convert_ai_route`）使用同一套注入逻辑。
- 发布门禁 `resource_version_uses_oauth2` 仍只针对 public/personal：只开启应用通道的资源在旧数据面上降级为“只有旧入口”，不阻塞发布。
- 同步更新插件 schema fixture（[plugins.yaml](../src/dashboard/apigateway/apigateway/fixtures/plugins.yaml)）。

### 7.3 上线方式

数据面插件与 Dashboard 同一次上线，上线期间 Dashboard 停止操作（不允许编辑和发布），不设全局应用通道开关；网关级开关默认开启（3.5）。

配置与插件的兼容关系：

| etcd 中的路由配置 \ 数据面插件 | 旧插件 | 新插件 |
| --- | --- | --- |
| 旧配置（升级后未重新发布） | 现状 | 兼容；未注入 OAuth2 插件的路由等同现状，personal/public 路由按 bkauth 规则分流（见下） |
| 新配置（升级后发布过） | **不兼容** | 正常 |

“旧配置＋新插件”对 personal/public 路由**不等同 `master`**（PR-1，已确认接受）：

- 命中规则的 Bearer 进入 OAuth2 链，格式或自省失败时拒绝，不回退 cookie 或旧凭证（与现状一致）。
- 未命中规则的 Bearer 视同缺少 OAuth2 凭证：符合条件的 cookie 仍可完成认证并保留后端自有 Bearer；没有可用旧入口时仍返回 401 挑战。现状是这类 Bearer 一律进入自省并被拒绝。
- 未配置 `bearer_token_rules` 时，personal/public 路由把所有可解析的 Bearer 都当作 bkauth Bearer，与现状一致；所以数据面必须带上 Helm 规则，并按实际配置验证存量 personal/public token 和后端自有 Bearer。

“不兼容”指：新转换器对网关开关开启且 A=1 的资源（包括旧默认配置和仅应用认证）注入 OAuth2 插件，并带上 `support_app` 和“缺少凭证时交给旧流程”的配置。旧插件忽略这两个字段，于是：

- 没有任何认证头、凭证放在 query/body 中的调用被 `bk-oauth2-protected-resource` 返回 401（4.1 描述的回归）；
- 非 bkauth Bearer 被当作 OAuth2 凭证自省后返回 401；
- 用户委托 token 和应用 token 被旧的 `bk-oauth2-appcode-validate` 拒绝。

上线顺序：

1. Dashboard 停止编辑和发布，同时暂停运维 CLI 重发（如 `sync_releases_to_gateway_parallel`），确认在途下发任务结束。
2. **先升级所有数据面插件。** 此时 etcd 中都是旧配置，处于“旧配置＋新插件”（行为差异见上）。逐个确认承接流量的实例已运行本次镜像，并加载了有效的 Helm 规则 `bk_gateway.bk_oauth2.bearer_token_rules`。APISIX 内核同为 3.18，以实际运行的镜像确认插件版本。
3. 确认所有数据面都运行新镜像后，执行迁移 `0059` 并升级 Dashboard。
4. 恢复 Dashboard 操作和 CLI；各网关在下一次发布时切换为新配置。

前提与原因：

- **新插件的新字段缺省值等于现状**：`support_app` 缺省为 false；`challenge_on_missing_credential` 缺省为 true（personal/public 路由的现状）。除上面的 Bearer 分流变化外，第 2 步的中间态是安全的；测试覆盖“不带新字段的旧配置”。
- 插件 schema 不禁止未知字段，旧版插件会忽略 `support_app` 和 `challenge_on_missing_credential`。`DataPlane.apisix_version` 只记录内核版本，Dashboard 无法据此识别插件镜像的新旧，所以**所有数据面必须先完成镜像升级，Dashboard 才能升级**。
- 网关运维已确认所有环境的 APISIX 都是 3.18，本次上线统一升级 3.18 镜像即可。7.2 中按 `apisix_version >= 3.16` 注入的判断保留，作为防御，避免将来接入低版本数据面时下发其不认识的插件。
- 改转换器不会改写 etcd 中已有路由；上线后各网关在下一次发布时才生效，scope 接口在网关重新发布前就可能列出资源（见 5.5）。

上线顺序的具体检查项见 7.5。

### 7.4 回滚

回滚的原则是**先恢复配置，再降级插件**，任何时候都不能出现“新配置＋旧插件”。

- 只回滚数据面镜像不够：已发布网关在 etcd 中的新配置不会随镜像回滚而改变。
- 只回滚资源版本也不够：Dashboard 仍是新版本时，新转换器会从旧快照的 A 推导出应用通道，重新发布后仍是新配置。
- 只需关闭个别网关的应用通道时（例如某网关出现误授权），关闭该网关的开关并重新发布其各环境即可，不需要回滚 Dashboard 或插件。路由上仍保留 personal/public 的配置，旧入口行为不变。

按问题位置选择回滚范围：

| 问题位置 | 处理 |
| --- | --- |
| 个别网关的应用通道 | 关闭网关开关并重新发布该网关各环境 |
| Dashboard（推导、归一化、scope 接口等） | 只回滚 Dashboard，保留新插件；按下文第 1～6 步恢复已发布环境（第 6 步不降级插件） |
| 数据面插件 | 优先修复后向前发布；必须降级插件时，先完成 Dashboard 回滚和第 1～6 步的恢复与核验，再降级插件 |

回滚步骤：

1. **暂停新增下发**：Dashboard 停止编辑和发布，暂停运维 CLI 重发，确认在途下发任务结束。时间 T 取新版 Dashboard **最早可能开始下发**的时间（不是升级完成时间）。
2. **生成数据库候选**（仍在新版 Dashboard 上）：按网关取 `ReleaseHistory.created_time >= T` 与 `Release.updated_time >= T` 的并集。CLI 和部分运维命令不写 `ReleaseHistory`，但成功下发会更新 `Release.updated_time`；`publish_id=-1` 可用于排查来源，两者都不能唯一识别一次 CLI 发布。
3. **独立扫描 etcd 原始路由**：扫描相关控制面和所有相关数据面 etcd 的原始路由配置，不能只依赖数据库候选。识别路由插件中**显式存在**的 `support_app` 或 `challenge_on_missing_credential`，值为 `false` 也计入；从路由标签取网关和环境，数据面取扫描目标。恢复范围 = 第 2 步候选 ∪ 本步扫描结果。
4. **回滚 Dashboard 到旧版本**，保留已完成的 `0059`，不执行反向迁移（新列带数据库默认值，见第 6 节）。旧转换器不会生成 `support_app` 和 `challenge_on_missing_credential`。若 bkauth 已接入新 scope 类型，同步暂停新 scope 入口。同一发布中其他保留的迁移也要满足“新列有数据库默认值”，否则旧代码写入失败：例如 `0058_resource_deprecation` 的 `deprecated_note` 只有 Django 侧默认值，回滚到 v1.25.0 后旧 Dashboard 同步或创建资源会报 `Field 'deprecated_note' doesn't have a default value`。
5. **用旧 Dashboard 重发恢复范围**内各环境的当前生效版本。v1.25.0 镜像使用 Python 3.14，`multiprocessing` 默认启动方式为 forkserver，`sync_releases_to_gateway_parallel` 的子进程会因 `AppRegistryNotReady` 卡住，需按下方片段强制使用 fork。
6. **核验后再降级插件**：再次扫描控制面和数据面 etcd，确认新版字段已清除，且 APISIX 已加载恢复后的路由；有失败或核验不通过的环境，保持新插件，先处理该环境。之后按需降级数据面插件，恢复 Dashboard 操作。若继续使用新插件，已有 personal/public 路由按 7.3 分流。
7. **再次升级时**：如降级过 APISIX，按 7.3 的首次升级顺序恢复；等旧 Dashboard 实例和发布任务全部退出后，执行第 6 节的 `sync_released_resource --all --oauth2-app-flags` 补算投影，再重发回滚期间由旧 Dashboard 下发过的网关（候选取 `--released-since T2`，T2 为旧 Dashboard 最早可能开始下发的时间，第 5 步的重发也在其中）。这些网关在 etcd 中仍是旧转换器生成的路由，补算后 scope、lookup 已显示应用通道，但数据面要重发后才生效。最后验收 scope、lookup 和实际调用。

第 2、5、7 步使用管理命令 `sync_releases_to_gateway_parallel`（旧版本 Dashboard 已有该命令和 `--gateway-names` 参数；本期新增 `--released-since`、`--dry-run`）：

```bash
# 第 2 步，仍在新版本 Dashboard 上（此时已暂停下发，列表不会再变化）：
# stdout 为空格分隔的网关名，stderr 输出 "N gateways matched"；没有命中时 stdout 为空
python manage.py sync_releases_to_gateway_parallel --released-since "<T，如 2026-11-17T10:00:00+08:00>" --dry-run > gateways.txt
# 与第 3 步 etcd 扫描得到的网关合并去重后写回 gateways.txt

# 第 5 步，在旧版本 Dashboard 上（bash）。旧命令的 --gateway-names 收到空列表时会同步全部网关，
# 所以按解析出的网关名数量判断，空文件或只有空白字符时都不调用。
# 直接执行该命令会在 forkserver 子进程中卡住，经 manage.py shell 强制 fork 后调用：
read -r -d '' -a gateway_names < gateways.txt || true
if [ "${#gateway_names[@]}" -gt 0 ]; then
  GATEWAY_NAMES="${gateway_names[*]}" python manage.py shell -c '
import multiprocessing, os
multiprocessing.set_start_method("fork", force=True)
from django.core.management import call_command
call_command("sync_releases_to_gateway_parallel", gateway_names=os.environ["GATEWAY_NAMES"].split())
'
else
  echo "no gateway to restore"
fi

# 第 7 步，在新版本 Dashboard 上补算投影之后：
python manage.py sync_releases_to_gateway_parallel --released-since "<T2>" --dry-run > gateways.txt
# 再用与第 5 步相同的片段重发 gateways.txt 中的网关
```

按网关重新发布覆盖该网关全部环境和绑定数据面，范围大于实际受影响的（网关、环境、数据面），但对未变化的环境是幂等的。命令对失败的网关返回非零并列出网关名，按第 6 步处理。

回滚验收覆盖：只有 CLI 重发、没有新增 `ReleaseHistory` 的网关；新字段已写入 etcd、数据库无更新的情况（由第 3 步扫描发现）；清单为空文件或只有空白字符。

### 7.5 上线运维验收

1. **首次升级（D2 / R1）**：按 7.3 的顺序。暂停常规发布和运维 CLI 重发并等在途任务结束；先升数据面，逐个确认承接流量的实例运行本次镜像并加载有效的 Helm 规则；随后执行迁移、升级 Dashboard，再恢复发布。
2. **回滚期间（PR-3 / PR-4）**：先回滚 Dashboard 并保留 `0059`，按 7.4 恢复并核验路由，再按需降级插件。仍使用新插件时，已有 personal/public 路由按 7.3 分流。bkauth 已接入新 scope 时，同步暂停新 scope 入口。
3. **再次升级（PR-4）**：降级过 APISIX 时按首次升级顺序恢复；旧 Dashboard 实例和发布任务全部退出后补算投影，再重发回滚期间由旧 Dashboard 下发过的网关。验收顺序为“升级并执行 0059 → 保留迁移回滚 → 旧代码首次发布新版本 → 再次升级并补算 → 重发”，核对用户委托 token、应用 token 两类标记，确认 scope、lookup 读到重新计算的值，应为 false 的资源仍为 false，重发后应用 Bearer 实际调用成功。
4. **升级后（D4 / D9 / Δ4）**：保持 `bk-apigateway.oauth2_app_enabled=true`，抽测 MCP 用户态和应用态入口。目标环境重发并确认 APISIX 加载后，抽测旧认证头、query/body、personal/public 和新增应用 Bearer。scope 或 lookup 可能先于路由显示能力，验收以实际调用为准。
5. **bkauth 自省与格式校验性能（D7）**：确认自省容量和现有限流，首批重发后观察自省 QPS、延迟、错误率。单独用实际 Helm 规则测前缀与格式校验开销，隔离自省网络耗时，观察吞吐、CPU 和 P99 延迟。
6. **MySQL 性能（I11 / I12）**：用接近生产的数据量演练 `0059` 的索引构建耗时和锁等待。保留应用通道索引，对 `app_delegated`、`app_only` 的查网关和查资源语句做 `EXPLAIN`，重点看分页前的候选网关扫描量和实际使用的索引。

## 8. MCP 边界

`bk-apigateway` 网关的 MCP 入口定义在 [bk-apigateway-resources.yaml](../src/dashboard/apigateway/apigateway/data/apigw-definitions/bk-apigateway-resources.yaml)：

| 入口 | 认证配置 | 推导结果 |
| --- | --- | --- |
| 用户态 `/api/v2/mcp-servers/{name}/sse`、`/sse/message`、`/mcp` | A=1、U=1、`resourcePermissionRequired=false`，public/personal 开启 | `auth_type=user`，app 默认开启 |
| 应用态 `/api/v2/mcp-servers/{name}/application/...` | A=1、U=0、`resourcePermissionRequired=false` | `auth_type=app`，接受应用 token |

本期处理：

- **用户态入口接受用户委托 token，应用态入口接受应用 token，都不允许关闭。** 这些是系统内置资源，认证配置由定义文件固定，不提供关闭入口；按 3.3、7.2 推导即为开启，与其他资源同一规则，不需要额外字段或特殊判断。用户态入口拒绝应用 token，应用态入口拒绝用户委托 token（4.2）。
- **不受业务网关开关影响。** 业务网关的开关只控制该网关自己的业务 API。MCP Server 走 `bk-apigateway` 网关的独立入口，按 MCP Server 权限授权；MCP Server 所属网关关闭开关，不影响该 Server 的应用通道：mcp-proxy 不区分调用来源，本期也不改 JWT 和 mcp-proxy。
- **平台运维保持 `bk-apigateway.oauth2_app_enabled=true`。** 关闭它会同时关闭所有 MCP 入口的用户委托 token 和应用 token 调用。
- **入口不校验资源权限，权限由 mcp-proxy 判断。** 入口 `resource_perm_required=false`；请求到达 mcp-proxy 后，`MCPServerPermissionMiddleware` 按网关 JWT 中的 app_code 查询 `MCPServerAppPermission` 并检查有效期（[mcp_permission.go](../src/mcp-proxy/pkg/middleware/mcp_permission.go)）。用户委托 token 和应用 token 的 app_code 都是真实应用，与旧认证头调用走同一份 MCP Server 授权，mcp-proxy 不需要改。
- **audience 接受 `mcp:{name}` / `mcp:*`，也接受网关范围 audience**（`gateway:*`、`gateway:bk-apigateway/api:*`、`gateway:bk-apigateway/api:{入口资源}`），由现有 `bk-oauth2-audience-validate` 校验，两种入口相同。这是有意的设计：MCP 入口本身是 `bk-apigateway` 网关的资源，网关范围 audience 自然覆盖它；能否访问具体 MCP Server 由 mcp-proxy 的 MCP Server 权限决定，网关不做细分。APISIX 单测锁定了该行为；如要收紧，须同时修改 bkauth 签发规则和 mcp-proxy。
- bkauth 签发约定：MCP scope 不新增 `app_only`；应用 token 调用 MCP 应用态入口可带 `mcp:{name}` / `mcp:*`，或经资源 scope 获得的 `bk-apigateway` 网关范围 audience。签发 `gateway:*` 等宽 audience 时，等同允许调用所有 MCP 入口（第 11 节）。
- **第二跳不变。** mcp-proxy 调用工具 API 时继续使用虚拟应用的 inner JWT，与旧认证头调用一致；本期不引入调研文档第 9 节的“委托来源”字段。
- **MCP Server 模型不新增应用通道开关，后续也不计划新增。** 所有者要禁止某应用调用，只能不给该应用授予 MCP Server 权限。bkauth 的 MCP scope 对 `app_delegated` 返回全部可见 MCP Server（5.5）。
- 应用态入口是 `auth_type=app`，按 3.1 注入插件并接受应用 token；没有 bkauth Bearer 时交给旧流程，旧认证头调用不变。

## 9. 改动清单

| 范围 | 文件 |
| --- | --- |
| 推导与校验 | `biz/resource/models.py`、`service/contexts/resource_auth.py`、`service/contexts/__init__.py`、`biz/resource/resource.py`（只读推导、层级约束含 `is_public`） |
| Web 接口：资源 | `apis/web/resource/serializers.py`（只读推导字段、批量更新的层级约束）、`views.py`（批量更新审计记录实际写入结果）；版本详情 `apis/web/resource_version/serializers.py` |
| Web 接口：网关 | `apis/web/gateway/serializers.py`、`biz/gateway/gateway.py`（网关开关读写） |
| 同步/导入 | `apis/v2/sync/serializers.py`（网关同步新增开关）；`apigw-definitions/bk-apigateway-resources.yaml`（接口定义）；openapi schema 不改 |
| 存储与发布投影 | `core/models.py`（`Gateway`、`ReleasedResource` 新列）、`core/constants.py`、迁移 `0059`（`db_default`、主键分页回填）、`core/managers.py`（投影写入与推导、排除绑定 `bk-access-token-source` 的资源、`refresh_oauth2_app_flags`） |
| 运维命令 | `controller/management/commands/sync_releases_to_gateway_parallel.py`（`--released-since` 取 `ReleaseHistory` ∪ `Release.updated_time`、`--dry-run`）；`core/management/commands/sync_released_resource.py`（`--oauth2-app-flags` 原地补算） |
| scope、lookup 与申请列表 | `service/oauth2_client_scope.py`、`service/gateway_released_resource.py`、`apis/v2/inner/serializers.py`、`views.py`（资源 lookup/list 新增两个输出字段、v2 申请列表规则 5.6）；`apis/open/permission/views.py`（v1 差异注释） |
| 下发 | `controller/convertor/route.py`（读取网关开关、`support_app`、`bk-access-token-source` 屏蔽、`challenge_on_missing_credential`）、`fixtures/plugins.yaml` |
| 版本差异 | `biz/resource_version/diff.py`（展示推导字段） |
| 文档 | `data/apidocs/zh/` 下 `v2_sync_gateway.md`、`v2_inner_list_oauth2_resource_scopes.md`、`v2_inner_list_oauth2_mcp_server_scopes.md`、`v2_inner_lookup_gateway_released_resources.md`、`v2_inner_list_gateway_released_resources.md`、`v2_inner_list_gateway_permission_resources.md`；仓库根 `docs/ddd-ubiquitous-language.md`；相关模块的 `AGENTS.md` |
| 前端 | 不在 #3543 范围；表单与提示文案按 3.1、4.4 另行交接 |
| mcp-proxy | 不改 |
| APISIX（#208） | `bk-core/config.lua`、`bk-core/oauth2.lua`、`bk-components/bkauth.lua`、`bk-oauth2-protected-resource`（含 `init()` 规则校验）、`bk-oauth2-verify`、`bk-oauth2-appcode-validate`、`bk-auth-validate`，以及对应 Busted、test-nginx（含完整插件链 `t/bk-oauth2-token-mode-chain.t`）和 `ci/run-test-nginx.sh` 的测试规则；`bk-oauth2-audience-validate` 不改，补 MCP 路径网关范围 audience 的单测 |

上表 Dashboard 路径相对 `src/dashboard/apigateway/apigateway/`。

## 10. 测试矩阵

| 场景 | 预期 |
| --- | --- |
| 存量四种旧配置读取 | `auth_type`、`oauth2_app_delegated_enabled` 按 3.1 推导 |
| 新表单四种映射＋personal/public 组合保存后再读取 | 往返一致 |
| Web、同步提交 `auth_type`、`oauth2_app_delegated_enabled` | 忽略，不影响存储 |
| U=false 且开启 personal 或 public | 400 |
| A=false 时传 `resource_perm_required=true` | 保存为 false |
| P=false 或 `is_public=false` 时传 `allow_apply_permission=true`（Web、同步） | 保存为 false |
| 关闭 `is_public` 再打开 | `allow_apply_permission` 保持 false |
| 资源批量更新对不满足层级的资源设置 `allow_apply_permission=true` | 静默写 false，其他资源正常写入 |
| Web 更新省略 `app_verified_required`、`resource_perm_required` | 保留当前存储值 |
| 旧 yaml 省略认证字段 | 用户认证＋OAuth 授权＋白名单 |
| 同步 yaml 只含旧字段 | 与改造前一致；schema 不变 |
| 导出后导入旧版本网关 | 成功（无新字段） |
| `ReleasedResource` 回填与发布写入 | `oauth2_app_delegated_enabled` 与 U && A、`oauth2_app_only_enabled` 与 !U && A 一致，不受网关开关影响 |
| 网关创建、迁移后存量网关 | 开关为 true |
| 网关同步 API 未传开关 | 新建为 true；已有网关保留当前值 |
| 迁移后用旧版 Dashboard 代码创建网关 | 成功，开关取数据库默认值 true |
| scope `app_delegated` | 返回 U && A、公开、且网关开关开启的资源 |
| scope `app_only` | 返回 !U && A、公开、且网关开关开启的资源；同一版本内与 `app_delegated` 不重叠 |
| scope：同一资源在两个环境分别发布为用户委托、仅应用 | `app_delegated`、`app_only` 下都列出（并集） |
| 投影：资源绑定 `bk-access-token-source`（`source=bearer`、省略、`api_key` 且 `allow_fallback` 为 true 或 false） | 两列都为 false；发布写入、`0059` 回填、补算一致 |
| scope `app_delegated` / `app_only`：网关开关关闭、尚未重新发布 | 不列出该网关资源（数据面仍接受，属预期时间差） |
| 资源 lookup/list 的 `oauth2_app_delegated_enabled`、`oauth2_app_only_enabled` | 等于对应新列 && 网关开关；非公开资源同样返回 |
| MCP scope `app_delegated` | 返回全部可见 MCP Server，不按开关筛选，不受所属网关开关影响 |
| MCP scope `app_only` | 不支持（参数校验失败） |
| MCP lookup/list | 不含 app 字段 |
| v2 申请列表 | `P=1` 且 A=1、允许申请的资源返回；`P=0` 的资源（含无需认证）返回 `unlimited`；未公开、`P=1` 但不允许申请的资源不出现（5.6） |
| v1 申请列表 | 仍只按 `allow_apply_permission` 筛选 |
| 批量更新部分资源不满足层级 | 审计 `allow_apply_permission_result` 按 true/false 分组记录资源 ID |
| 转换器：仅应用认证的资源 | 注入 OAuth2 插件，`support_app=true`，不返回 401 challenge |
| 转换器：网关开关关闭 | 不生成 `support_app`；只开启应用通道的资源（含仅应用认证）不注入插件；开启 personal/public 的资源注入但 `support_app=false` |
| 转换器：AI 资源 | 与标准资源相同的注入与 `support_app` |
| 转换器：绑定 `bk-access-token-source`（`source=bearer`、省略、`api_key` 且 `allow_fallback` 为 true 或 false） | 未开 personal/public 时不注入 OAuth2 插件；已开时注入且 `support_app=false`；标准与 AI 资源相同 |
| 有权应用的用户委托 token，aud 命中，带用户 | 通过 |
| 无权应用的用户委托 token（白名单开启） | 拒绝 |
| 白名单关闭，任意应用的用户委托 token | 通过 |
| 用户认证资源：应用 token | 401 ＋ `WWW-Authenticate`，原因为只接受用户委托 token（完整插件链验证） |
| 用户认证资源：`sub == client_id`，`username` 为非空字符串，其他校验通过 | 判为用户委托 token，放行 |
| 真实应用 token 的 `sub` 或 `client_id` 缺失、为空或不是字符串，或 `username` 缺失、为 `null` 或其他非字符串 | 模式为 `unknown`，401；personal/public 不受影响 |
| 用户认证资源：免用户认证应用、skip 命中的用户委托 token | 仍要求有效用户 |
| 仅应用认证资源：有权应用的应用 token，aud 命中 | 通过；后端 JWT 中用户为空且未认证，不出现 `client_id` 作为用户名 |
| 仅应用认证资源：无权应用的应用 token（白名单开启） | 拒绝 |
| 仅应用认证资源：应用 token 的 aud 不含该资源 | 403（`invalid_audience`） |
| 仅应用认证资源：用户委托 token | 401 ＋ `WWW-Authenticate`，原因为只接受应用 token（完整插件链验证） |
| 仅应用认证资源：query/body 应用凭证、`X-Bkapi-Authorization`、非 bkauth Bearer | 走旧流程，结果与改造前一致，非 bkauth Bearer 透传 |
| OAuth 授权关闭时的用户委托 token | 拒绝；personal/public 不受影响 |
| 网关关闭开关并重新发布后的用户委托 token、应用 token | 拒绝；同时不满足用户要求时由 `bk-auth-validate` 先返回用户校验错误。旧认证头与 personal/public 不受影响 |
| 多租户：用户委托 token 应用租户与网关租户不匹配 | 由现有多租户插件拒绝 |
| 只开启应用通道的路由：query/body 认证参数、无凭证 | 走旧流程，结果与改造前一致 |
| 开启 personal/public 的路由：无凭证 | 401 和 WWW-Authenticate（不变） |
| 已注入插件的路由：无效 Bearer＋有效登录态 cookie | 拒绝，不回退旧流程 |
| 三项全关（仅用户认证）：过期 Bearer＋有效登录态 cookie | 按 cookie 认证通过；`Authorization` 原样透传后端 |
| 三项全关：只带 Bearer | 按旧链路结果处理（缺少用户凭证时拒绝） |
| 已注入插件的路由：query/body 应用凭证＋非 bkauth Bearer | 走旧流程，Bearer 透传后端 |
| 已注入插件的路由：`X-Bkapi-Authorization`＋非 bkauth Bearer | 走旧流程，Bearer 透传后端 |
| 开启 personal 的路由：只带非 bkauth Bearer | 401 和 WWW-Authenticate（视同无凭证） |
| 开启 personal 的路由：非 bkauth Bearer＋有效登录态 cookie（仅用户认证） | 走 cookie 分支，Bearer 透传后端 |
| 带 bkauth 前缀但无效、过期的 token | 拒绝，不回退旧流程 |
| `bkp_` 等前缀命中但长度或字符不符 | 401，不调用自省，不回退 |
| `bkx_...`（类型码不在 `oprs`）、`bk_...`、`tai_` 等相近但不命中的 Bearer | 视为非 bkauth Bearer，走旧流程并透传 |
| `tai_pat_` 前缀的 token | 交给 bkauth 自省，按自省结果走 personal/public/app 同一校验链 |
| `bkr_` refresh token 当作 Bearer 使用 | 自省拒绝，401，不回退 |
| 修改前缀配置 | 重新加载配置后生效，不需要改插件代码 |
| 非法 `prefix_pattern` | 记录 error，跳过该规则，继续匹配后续规则 |
| `format_pattern` 是字符串但无法编译 | 记录 error，按格式不符返回 401 |
| 提供了非字符串 `format_pattern` | 加载时记一条 error，命中前缀的 token 按格式不符返回 401 |
| `bearer_token_rules` 不是列表（布尔、字符串、数字、对象） | 加载时记一条 error，请求阶段按未配置处理（同 nil） |
| 插件加载：规则非法（非列表、非对象、正则非字符串或不可编译） | 每个问题记一条 error，启动不受影响；规则未配置记 warn |
| 未配置 `bearer_token_rules`：只开启应用通道的路由收到任意 Bearer | 走旧流程，按资源要求认证 |
| 未配置 `bearer_token_rules`：personal/public 路由收到任意 Bearer | 进入 OAuth2 流程（与改造前一致） |
| 存量 personal/public token | 符合当前规则，调用结果与改造前一致 |
| 低于 3.16 的数据面（转换器单测，当前环境无此版本） | 不注入 OAuth2 插件，发布不被只开启应用通道的资源阻塞 |
| MCP 用户态入口：有 MCP Server 权限的应用的用户委托 token，aud 为 `mcp:{name}` | 通过 |
| MCP 用户态入口：无 MCP Server 权限或权限过期的应用 | mcp-proxy 拒绝 |
| MCP 用户态入口：用户委托 token 的 aud 不含该 Server | 网关拒绝 |
| MCP 应用态入口：有 MCP Server 权限的应用的应用 token，aud 为 `mcp:{name}` | 通过 |
| MCP 应用态入口：用户委托 token | 网关拒绝 |
| MCP 入口：aud 为 `gateway:*`、`gateway:bk-apigateway/api:*` 或该入口资源 | 网关放行，由 mcp-proxy 校验 MCP Server 权限；其他网关的 aud 403 |
| MCP 应用态入口：旧认证头调用 | 行为不变 |
| 新插件＋不带新字段的旧路由配置：无 OAuth2 插件的路由 | 与改造前一致 |
| 新插件＋不带新字段的旧路由配置：personal/public 路由 | 命中规则的 Bearer 与改造前一致；未命中规则的 Bearer 视同无凭证，有符合条件的 cookie 时走 cookie 认证，否则 401 挑战（7.3） |
| 同一新插件和规则下显式下发 `challenge_on_missing_credential: true`、`support_app: false` | 与省略这两个字段相同 |
| 迁移后用旧版 Dashboard 代码发布 | `ReleasedResource` 写入成功，新列取数据库默认值 false |
| 回滚演练：新 Dashboard 发布后回滚 Dashboard，并用旧 Dashboard 重新发布 | etcd 路由不含 `support_app` 和 `challenge_on_missing_credential`；旧插件下 query/body 认证调用正常 |
| 回滚候选：只有 CLI 重发、无新增 `ReleaseHistory` 的网关 | `--released-since` 通过 `Release.updated_time` 列出 |
| 回滚候选：新字段已写入 etcd、数据库无更新 | 由 etcd 原始路由扫描发现（7.4 第 3 步） |
| 回滚候选：清单为空 | `--dry-run` 的 stdout 为 0 字节；回滚脚本对空文件、只有空白字符的文件都不调用旧命令（避免空 `--gateway-names` 走全量） |
| 再次升级补算：旧 Dashboard 回滚期间首次发布的版本 | `sync_released_resource --all --oauth2-app-flags` 后两列等于推导值，应为 false 的仍为 false；scope、lookup 读到新值；可重复执行；按 `--released-since T2` 重发后应用 Bearer 调用成功 |

## 11. 待确认

以下外部事项都**不阻塞合并**，上线前逐项确认；联调在本地 Minikube 完成。

| 问题 | 负责方 | 影响 |
| --- | --- | --- |
| 用户委托 token 的 audience 能否带上 `gateway:{网关}/api:{资源}` | bkauth | 不能则 audience 校验全部拒绝 |
| 是否为普通蓝鲸应用签发应用 token（`client_credentials` grant）；签发后验证自省字段符合 4.2，确认其 audience 能否按 `app_only` scope 选择并带上 `gateway:{网关}/api:{资源}` | bkauth | 决定本期仅应用认证资源的 Bearer 调用能否打通 |
| 应用 token 调用 MCP 应用态入口时带哪种 audience：`mcp:{name}` / `mcp:*`，或 `bk-apigateway` 网关范围 audience（MCP scope 不新增 `app_only`） | bkauth | 两者网关都接受（第 8 节）；都拿不到则 MCP 应用态入口的 Bearer 调用被 audience 校验拒绝 |
| 签发约定：`gateway:*`、`gateway:bk-apigateway/api:*` 这类宽 audience 也覆盖所有 MCP 入口，MCP Server 权限由 mcp-proxy 判断 | bkauth | 授权页需向用户说明宽 audience 的覆盖面 |
| scope 是各环境的并集，同一资源可能同时出现在 `app_delegated` 和 `app_only` 下；lookup 只显示所读版本的模式 | bkauth | 授权页不能假设两种类型互斥（5.5） |
| 用户委托/应用模式的判定字段（`sub`、`client_id`、`username`）是否稳定；个人令牌（含 `tai_pat_`）是否总带 `client_id` | bkauth | 确认存量 token 的自省字段；personal/public 仍按各自规则校验 |
| `app_delegated` / `app_only` scope 规模与授权页分页；scope 类型取值对齐 | bkauth | 5.5 |
| 网关开关在 scope 上立即生效、数据面需重新发布的时间差；非公开对象手填与资源 lookup 新字段 | bkauth | 5.5 |
| 是否签发 `gateway:*` / `mcp:*` 通配 audience | bkauth | 通配 audience 覆盖面 |
| `tai_pat_` 自省返回的 `bk_app_code` 取值 | bkauth | 决定 `tai_pat_` token 走 personal/public 还是真实应用分支 |
| 生产自省容量与负缓存策略 | bkauth | 首批重发后自省 QPS 上升（7.5 第 5 项） |
| 绑定 `bk-access-token-source` 的线上资源数量（已知为个位数） | 网关运维 | 7.2 屏蔽规则的影响面 |

已关闭（2026-11-18 代码评审决策）：

| 编号 | 结论 |
| --- | --- |
| I6 | `client_id` 与 `bk_app_code` 各自保留语义，应用身份以自省返回的 `bk_app_code` 为准 |
| I10 | `auth_verified_required`、`app_verified_required` 在资源快照中始终存在，缺省差异无需处理 |
| I14 | 保留 personal/public 必须开启用户认证的规则；现网无违反该规则的历史快照 |
| Δ3 | bkauth 确认 personal/public token 不会同时满足 `sub == client_id` 且 `username` 为空，沿用 personal/public 的校验规则 |
| D4 / D8 | 已确认没有业务依赖 bkauth Bearer 透传给后端 |

已确认（bkauth，2026-11-17）：

| 问题 | 结论 | 对方案的影响 |
| --- | --- | --- |
| 存量 personal/public token 是否都符合 `bk[oprs]_[0-9A-Za-z]{36}` 或 `tai_pat_` | 是 | 前缀匹配不影响存量 personal/public 调用 |
| `tai_pat_` token 的来源，是否走同一个 bkauth 自省接口、返回字段是否一致 | bkauth 对接外部认证太湖签发；与 bkauth token 走相同的认证接口，返回字段一致 | 复用同一校验链（4.2），网关不单独处理；前缀之后的格式未约定，不配置本地格式校验，由自省判定 |
| 类型码 `r` 是否是 refresh token，自省是否拒绝其作为 access token | 是 | `bkr_` 命中前缀后交给自省，由自省拒绝，网关不单独处理 |

已确认（2026-11-19 评审）：应用自身 token 的自省 `username` 是空字符串 `""`，SaaS 用户委托 token 的 `sub` 可能等于 `client_id`。

已确认（网关运维，2026-11-17）：

| 问题 | 结论 | 对方案的影响 |
| --- | --- | --- |
| 各环境数据面的 APISIX 版本 | 全部为 3.18 | 7.3 只需统一升级 3.18 镜像；低版本兼容判断仅作防御 |

## 12. 发布说明（草案）

实现完成后，按下列内容整理进 `data/version_log/CHANGELOG.md` 和对外发布说明。

### 新增

- 资源认证配置改为“认证类型”：无需认证、用户认证、应用认证。用户认证下可选择个人令牌、公开客户端、OAuth 授权。
- 新增“OAuth 授权”：蓝鲸应用经用户授权后，可用 `Authorization: Bearer <token>` 以该用户身份调用资源。权限沿用现有应用权限，不需要重新申请。
- 仅应用认证的资源支持蓝鲸应用以应用 token（`client_credentials` grant）通过 `Authorization: Bearer <token>` 调用，权限沿用现有应用权限。
- 新增网关级“OAuth 应用通道”开关，默认开启，网关管理员可按网关关闭；网关同步 API 支持该字段。
- 同步 API 和资源导入的格式不变；资源接口新增只读字段 `auth_type`、`oauth2_app_delegated_enabled`。
- bkauth 内部资源 scope 接口支持 `oauth_client_type=app_delegated`、`app_only`，MCP scope 接口支持 `app_delegated`；已发布资源 lookup/list 接口新增 `oauth2_app_delegated_enabled`、`oauth2_app_only_enabled`。

### 行为变化

- **存量“应用＋用户认证”的资源，在网关下一次发布后会开放 OAuth 授权；存量“仅应用认证”的资源会开放应用身份 token 调用。** 有该资源权限的应用可以用 Bearer 调用；没有权限的应用仍被拒绝（白名单开启时）。不希望开放的网关可以关闭网关开关后重新发布。
- **仅应用认证的资源上，带 bkauth 前缀的 Bearer 会被网关拦截校验，不再透传给后端。** 其他 Bearer 仍透传。
- **网关只处理 bkauth 签发的 Bearer token（前缀为 `bk[oprs]_` 或 `tai_pat_`）。** 后端自有的 `Authorization: Bearer` 不会被网关拦截或删除，仍按资源的认证配置走旧方式，并原样透传给后端。
- **已开启个人令牌/公开客户端的资源，升级数据面后即按上述规则区分 Bearer，不需要重新发布。** 后端自有 Bearer 不再被直接拒绝：有登录态 cookie 时按 cookie 认证，没有其他凭证时仍返回 401。关闭网关的 OAuth 应用通道不改变这项行为。
- **绑定了 `bk-access-token-source` 插件的资源不开放 OAuth 应用通道**，行为与升级前相同。
- **OAuth 应用 token 与资源要求不匹配时返回 401。** 要求用户的资源只接受用户委托 token，仅应用认证的资源只接受应用 token；响应带 `WWW-Authenticate` 和失败原因。audience 不匹配仍为 403。
- **客户端只携带一种网关认证凭证。** 同时携带旧认证头和 Bearer 时走旧方式，未被网关消费的 Bearer 会透传给后端。
- **在页面上关闭“OAuth 授权”，会同时影响旧版调用方式。** 资源不再校验应用身份和应用权限，只校验用户身份。
- **“校验应用权限”“允许申请权限”依赖上层配置。** 关闭应用认证时，这两项自动关闭；“允许申请权限”还要求资源公开。首次编辑、同步或导入存量资源时，可能因此在预览、版本对比和导出中看到差异。
- **开发者中心资源列表（v2）**：不校验应用权限的公开资源（仅用户认证，或应用认证但关闭应用白名单）也会列出，权限级别为“无需申请”；仍校验应用权限但不允许申请的资源不再出现。
- 未开启任何 OAuth2 选项的资源行为不变：网关不识别 Bearer，`Authorization` 头原样透传给后端。

### 升级要求

- 数据面插件与 Dashboard 必须同时升级，上线期间 Dashboard 停止编辑和发布，并暂停运维 CLI 重发。先升级所有数据面（APISIX 3.18）到包含新插件的镜像，并确认加载了 Helm 下发的 `bk_gateway.bk_oauth2.bearer_token_rules`，再升级 Dashboard，否则旧默认配置的资源在发布后可能出现 401。
- 升级后配置不会自动改写已有路由，各网关需重新发布才生效。
- 回滚时先回滚 Dashboard（保留迁移 0059），按 7.4 找出并用旧 Dashboard 重新发布受影响的环境，核验 etcd 与 APISIX 加载结果后才能降级数据面插件；不能只回滚数据面镜像或资源版本。只需关闭个别网关时，关闭网关开关并重新发布即可。
- 回滚后再次升级，需执行 `sync_released_resource --all --oauth2-app-flags` 补算已发布资源投影（第 6 节），并重发回滚期间由旧 Dashboard 下发过的网关（7.4 第 7 步）。
- 平台保持 `bk-apigateway` 网关的 OAuth 应用通道开启，否则 MCP 入口的 Bearer 调用不可用。

## 附录：决策记录

| 决策 | 结论 |
| --- | --- |
| 事实来源 | 新表单/新模型；表单映射为旧字段写入，接口上的新字段由旧字段推导 |
| 兼容边界 | 兼容旧格式与旧调用方式，不冻结修改前的认证要求 |
| 应用通道的语义 | 用户委托 token：应用经用户授权后以该用户身份访问，必须认证用户、认证应用；应用 token：应用以自身身份访问，只用于仅应用认证的资源 |
| 命名 | `app_` 前缀表示真实蓝鲸应用作为客户端，后缀区分是否带用户：`oauth2_app_delegated_enabled` / scope `app_delegated`（用户委托 token），`oauth2_app_only_enabled` / scope `app_only`（应用 token）；网关开关 `Gateway.oauth2_app_enabled` 覆盖两者；不按 OAuth2 grant 类型命名 |
| 应用通道注入 | `support_app = 网关开关 && A && 未绑定 bk-access-token-source`，覆盖用户认证与仅应用认证；接受的 token 模式由 `verified_user_required` 决定，Dashboard 不下发 token 类型，将来扩展只升级插件 |
| 旧路由＋新插件（PR-1） | 接受相对 `master` 的变化：personal/public 路由按 bkauth 规则分流，未命中规则的 Bearer 视同无凭证；网关开关只关闭真实应用 token |
| 规则缺失兜底（D1） | 未配置 `bearer_token_rules` 时，只开启应用通道的路由不拦截 Bearer，交给旧流程 |
| 失败响应（I3） | token 模式不匹配两个方向、真实应用 `unknown` 都返回 401 ＋ `WWW-Authenticate`；audience 不匹配 403；旧链路与 personal/public 不变 |
| 模式判定（I5 / #208 评审） | 按 4.2 判定 `delegated`、`app` 或 `unknown`。真实应用的 `unknown` 返回 401 |
| 回滚恢复范围（PR-3） | `ReleaseHistory` ∪ `Release.updated_time` 的数据库候选，再并上 etcd 原始路由扫描（显式字段，false 也计入）；核验 etcd 与 APISIX 加载后才降级插件；空清单不调用旧命令 |
| 再次升级（PR-4） | `sync_released_resource --oauth2-app-flags` 原地补算投影，可重复执行，不删除投影 |
| 0059（I11） | 主键分页回填；保留 `db_default`；DDL 用普通 `AddField`/`AddIndex`，不再先探测再执行 |
| v2 申请列表（I7 / I8） | 所有 `P=0` 的公开资源（含无需认证）都返回 `unlimited`；v1 不变，注释说明差异 |
| 规则加载时校验（R2 / #208 评审） | 插件 `init()` 校验并保存规则，按 7.1 记录配置问题，插件继续启动 |
| 投影与 `bk-access-token-source`（PR-2 / PR-7） | 绑定该插件即不开放应用通道，不区分 `source`、`allow_fallback`（严格 API Key 会在 OAuth2 校验前返回 400）；规则同时作用于路由与投影推导，scope、lookup、回填、补算一致；Web 只读字段仍为 U && A |
| 跨环境 scope（PR-5） | 接受各环境并集；不承诺两种类型互斥，实际以目标环境路由为准 |
| MCP audience（PR-6） | 不改代码：MCP 入口同时接受 `mcp:*` 类和网关范围 audience，MCP Server 权限由 mcp-proxy 负责；同步 bkauth 签发约定 |
| 外部依赖 | 第 11 节各项不阻塞合并，上线前确认；联调最后在 Minikube 完成 |
| 批量更新审计（I13） | 同时记录请求值和按 true/false 分组的实际写入结果 |
| 权限 | 复用现有应用权限，`resource_perm_required` 决定是否校验，不因 OAuth 强制开启 |
| 层级 | 应用认证 → 校验应用权限 → 允许申请权限；允许申请还要求 `is_public`；覆盖 Web、批量更新、同步、导入；存量数据不迁移 |
| `app_verified_required` | 保留，不新增 `Resource` 列 |
| 写入字段 | `auth_type`、`oauth2_app_delegated_enabled` 只读；写入只用旧字段，同步 yaml 不新增字段，无新旧字段冲突规则 |
| 未传与显式 false | 同步、导入与 Web 创建用旧默认值，Web 更新保留当前存储值 |
| 网关开关 | `Gateway.oauth2_app_enabled`，默认开启；网关管理员在页面和 v2 网关同步 API 修改；重新发布后在数据面生效；控制 Bearer 入口的用户委托 token 和应用 token |
| bkauth scope | 资源：`app_delegated` 按 `ReleasedResource.oauth2_app_delegated_enabled`（U && A）、`app_only` 按 `oauth2_app_only_enabled`（!U && A），都叠加网关开关当前值；MCP：只新增 `app_delegated`，返回全部可见 MCP Server，不按开关筛选；不按应用权限过滤 |
| 非公开对象 | scope 只列公开对象；非公开对象手填，用现有 lookup 接口校验；资源 lookup 新增 `oauth2_app_delegated_enabled`、`oauth2_app_only_enabled`，MCP lookup 不新增 |
| 导出 | 格式不变 |
| 全部 OAuth2 关闭时的 Bearer | 不注入插件，网关不识别、不拦截，只走旧链路；`Authorization` 透传后端 |
| 拦截哪些 Bearer | 只拦截前缀为 `bk[oprs]_` 或 `tai_pat_` 的 token（APISIX 侧配置）；前缀命中但格式不符直接拒绝；其他 Bearer 走旧配置并透传后端；无效 bkauth token 不回退旧流程 |
| token 模式识别 | `sub`/`client_id`/`username` 双信号判定用户委托与应用模式；要求用户的资源只接受用户委托 token，仅应用认证的资源只接受应用 token；两者都校验 audience |
| AI 资源、多租户、后端 JWT | AI 资源同规则；租户沿用现有插件；JWT 不区分调用来源 |
| 上线方式 | 数据面与 Dashboard 同时上线，期间 Dashboard 停止操作；不设全局开关；先升级数据面，再升级 Dashboard；不设压测门禁 |
| 回滚 | 先回滚 Dashboard 并重新发布受影响的环境，核验后才降级插件；新列带 `db_default`，回滚不需要反向迁移；个别网关用网关开关止血 |
| MCP | 平台保持 `bk-apigateway.oauth2_app_enabled=true`；不新增开关，后续也不计划；用户态入口接受用户委托 token、应用态入口接受应用 token，不允许关闭、不受所属网关开关影响；MCP scope 不新增 `app_only`；入口不查资源权限，由 mcp-proxy 校验 MCP Server 权限；audience 接受 `mcp:*` 类和网关范围 |
