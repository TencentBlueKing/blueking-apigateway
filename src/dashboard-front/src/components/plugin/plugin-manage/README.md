# 插件管理

## 目录结构

```text
plugin-manage/
├── Index.vue                         # 插件管理入口
├── README.md
├── config-editor/                    # 插件选择、配置编辑与提交
│   ├── Index.vue
│   ├── definitions.ts                # 插件编辑协议、提示和示例注册
│   ├── form-adapter.ts               # 表单协议适配、配置解析与序列化
│   ├── types.ts
│   └── components/
│       ├── PluginFormRenderer.vue
│       └── WhitelistTable.vue
└── config-display/                   # 插件配置只读展示
    ├── Index.vue
    ├── types.ts
    └── components/
        ├── BaseTable.vue
        ├── GenericTable.vue
        ├── HeaderRewriteTable.vue
        ├── IpRestrictionTable.vue
        ├── RateLimitTable.vue
        ├── EnabledTable.vue
        ├── TrafficLabelTable.vue
        └── QueryStringRewriteTable.vue
```

插件专用表单放在相邻的 `src/components/plugin/plugin-form/<插件 code>/` 中，统一直接使用 bkui-vue 组件渲染，
不再依赖 Schema 描述；多个表单共用的字段控件放在 `plugin-form/components/`。
`plugin-form/components/KeyValuePairs.vue`（键值对列表）供 `api-breaker`、`bk-mock`、`response-rewrite`、
`bk-query-string-rewrite` 和 `bk-header-rewrite` 共用；`plugin-form/components/KeysInput.vue`（键名列表）供
`bk-query-string-rewrite` 和 `bk-header-rewrite` 共用。
两者的键名格式默认只允许字母、数字、下划线和连字符，可通过 `keyRule`（`pattern` 与已翻译的 `message`）替换。
`KeyValuePairs` 操作按钮的上边距默认 4px，外层可设置 CSS 变量 `--key-value-pairs-actions-padding-top` 调整。
`bk-query-string-rewrite` 使用 `/^[^=&#?]+$/` 规则，并把该变量设为 8px；`bk-header-rewrite` 使用默认规则，变量同样设为 8px。
同一职责目录内使用相对导入，跨目录使用 `@/components/...` 路径。

## 模块职责

`config-editor/Index.vue` 负责插件选择、介绍、环境变更确认和接口提交。
`config-editor/components/PluginFormRenderer.vue` 负责配置初始化和表单渲染，对外暴露 `getYaml()`、`clearValidate()` 和 `isReady`。
插件接入方式集中登记在 `config-editor/definitions.ts`，渲染和提交共用该定义。

`config-display/Index.vue` 根据插件 code 选择展示表格，未单独配置的插件使用 `GenericTable.vue`。
`EnabledTable.vue` 展示无参数插件的启用状态，供多个插件共用。

## 新增插件

1. 在 `plugin-form/` 实现插件专用表单，保留布局、字段联动和业务配置转换。
2. 在 `config-editor/definitions.ts` 注册插件 code，选择对应的编辑协议；需要在表单上方展示提示时，传入 `notice`。
3. 如需要，补充示例及国际化词条；示例位于 `src/constants/plugin-form-examples.ts`。
4. 如需专用的只读展示，在 `config-display/components/` 实现表格，并在 `config-display/Index.vue` 登记映射。
5. 执行下列检查。无需在 `config-editor/Index.vue` 或公共提交函数中增加插件 code 分支。

| editor.kind | 输入 | 暴露方法 | 提交行为 |
| --- | --- | --- | --- |
| `custom` | `data` 配置对象 | `getValue()`，可选 `clearValidate()` | `getValue()` 自行校验并返回业务配置对象，公共层转 YAML |
| `whitelist` | `type`、`yamlStr` | `sendPolicyData()` 返回 `{ data, error }` | 检查转换结果，直接使用返回的 YAML |
| `none` | 无 | 无 | 显式提交 `'{}'` |

界面状态转业务配置的逻辑留在对应表单中，公共层只处理协议适配和 YAML 序列化。
`custom` 表单校验失败时由 `getValue()` 抛出异常，字段错误由表单自行展示。

未知插件不会被当作无参数插件，界面会阻止提交。
插件切换、配置切换会重建表单；语言切换只更新界面文案，保留当前草稿。
编辑配置统一使用详情接口的 `yaml`，不再通过父组件调用方法回填。

`bk-cors` 的字段名直接作为标签展示，字段说明使用 `bk_cors_<字段>_desc` 国际化词条。新增时使用推荐默认值；
编辑时按已保存的配置回显，缺失字段不套用默认值（`allow_credential` 缺失视为 `false`），提交时只输出插件支持的 7 个字段。
`allow_origins` 下展示两项联动校验：与 `allow_origins_by_regex` 不能同时为空、不能同时有效。

`bk-resource-user-rate-limit` 使用 `custom` 表单，直接使用 bkui-vue 的表单、输入框和选择框组件，不依赖 Schema 表单控件。
默认用户频率限制固定为一条，不提供添加、克隆或删除操作，提交时 `rates.__default` 始终为单元素数组。
同一用户名只能配置一条频率限制，次数或周期不同也不允许重复；不同用户可以配置完全相同的次数和周期。
提交时每个 `rates[用户名]` 都是单元素数组。旧配置中的多条规则会完整回显，修正重复用户名后才能提交。
用户名使用 `UserSelector`（`src/components/user/user-selector/`）单选：普通环境渲染 `StaffSelector`，多租户环境渲染
`BkUserSelector` 并使用当前租户的用户接口；提交时统一取用户名。

## 验证

从 `src/dashboard-front/` 执行：

```sh
pnpm type-check
pnpm lint:ci
pnpm build-only
```

UI 交互和实际接口需在运行环境验收。
