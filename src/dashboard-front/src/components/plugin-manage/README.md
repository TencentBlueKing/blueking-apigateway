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
├── config-display/                   # 插件配置只读展示
│   ├── Index.vue
│   ├── types.ts
│   └── components/
│       ├── BaseTable.vue
│       ├── GenericTable.vue
│       ├── HeaderRewriteTable.vue
│       ├── IpRestrictionTable.vue
│       ├── RateLimitTable.vue
│       ├── EnabledTable.vue
│       ├── TrafficLabelTable.vue
│       └── QueryStringRewriteTable.vue
└── schema-form/                      # Schema 表单渲染基础组件
    ├── Index.vue
    ├── types.ts
    ├── component-map.ts              # Schema 字段与运行时组件的映射
    └── components/
        ├── SchemaObjectField.vue
        ├── CustomAddDelForm.vue
        ├── InputComponent.vue
        ├── InputNumberComponent.vue
        ├── SelectComponent.vue
        └── SwitchComponent.vue
```

插件专用表单仍放在相邻的 `src/components/plugin-form/<插件 code>/` 中。
同一职责目录内使用相对导入，跨目录使用 `@/components/...` 路径。
类型从各目录的 `types.ts` 导入；运行时组件映射和表单适配逻辑分别维护。

## 模块职责

`config-editor/Index.vue` 负责插件选择、介绍、环境变更确认和接口提交。
`config-editor/components/PluginFormRenderer.vue` 负责配置初始化和表单渲染，对外暴露 `getYaml()`、`clearValidate()` 和 `isReady`。
插件接入方式集中登记在 `config-editor/definitions.ts`，渲染和提交共用该定义。

`config-display/Index.vue` 根据插件 code 选择展示表格，未单独配置的插件使用 `GenericTable.vue`。
`EnabledTable.vue` 展示无参数插件的启用状态，供多个插件共用。

`schema-form/Index.vue` 提供 Schema 字段渲染入口，`component-map.ts` 维护字段类型与组件的映射。
Schema 表单和插件专用表单可以复用该目录的字段控件。

## 新增插件

1. 在 `plugin-form/` 实现插件专用表单，保留布局、字段联动和业务配置转换。
2. 在 `config-editor/definitions.ts` 注册插件 code，选择对应的编辑协议。
3. 如需要，补充中英文 Schema、示例及国际化词条；现有 Schema 位于 `src/json/schemaPluginForm{Cn,En}.json`，示例位于 `src/constants/plugin-form-examples.ts`。
4. 如需专用的只读展示，在 `config-display/components/` 实现表格，并在 `config-display/Index.vue` 登记映射。
5. 执行下列检查。无需在 `config-editor/Index.vue` 或公共提交函数中增加插件 code 分支。

| editor.kind | 输入 | 暴露方法 | 提交行为 |
| --- | --- | --- | --- |
| `custom` | `data` 配置对象 | `getValue()`，可选 `clearValidate()` | `getValue()` 自行校验并返回业务配置对象，公共层转 YAML |
| `schema` | `v-model`、`schema`、`layout`、`routeMode` | `validate()`、`getValue()`，可选 `clearValidate()` | 先等待 `validate()` 返回真值，再取业务配置并转 YAML |
| `whitelist` | `type`、`yamlStr` | `sendPolicyData()` 返回 `{ data, error }` | 检查转换结果，直接使用返回的 YAML |
| `none` | 无 | 无 | 显式提交 `'{}'` |

`schema` 表示接入协议，不要求各插件使用相同布局。CORS、IP 限制、Header 改写和限流继续使用各自的专用组件。
界面状态转业务配置的逻辑留在对应表单中，公共层只处理协议适配和 YAML 序列化。

未知插件不会被当作无参数插件，界面会阻止提交。
插件切换、配置切换会重建表单；语言切换仅更新 Schema 和布局，保留当前草稿。
编辑配置统一使用详情接口的 `yaml`，不再通过父组件调用方法回填。

`bk-resource-user-rate-limit` 使用 `custom` 表单，直接使用 bkui-vue 的表单、输入框和选择框组件，不依赖 Schema 表单控件。
默认用户频率限制固定为一条，不提供添加、克隆或删除操作，提交时 `rates.__default` 始终为单元素数组。
同一用户名只能配置一条频率限制，次数或周期不同也不允许重复；不同用户可以配置完全相同的次数和周期。
提交时每个 `rates[用户名]` 都是单元素数组。旧配置中的多条规则会完整回显，修正重复用户名后才能提交。
普通环境使用 `MemberSelector`，多租户环境使用 `BkUserSelector` 和当前租户的用户接口；两种控件均为单选，提交时统一取用户名。

## 验证

从 `src/dashboard-front/` 执行：

```sh
pnpm type-check
pnpm lint:ci
pnpm build-only
```

UI 交互和实际接口需在运行环境验收。
