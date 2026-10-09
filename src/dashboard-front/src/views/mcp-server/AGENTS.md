# MCP 管理界面

- `components/CreateSlider.vue` 共用创建/编辑流程，基础表单由 `ServerBasicForm.vue` 承接，
  工具和提示选择在 Slider 内实现；`detail/Index.vue` 使用 `ServerTools.vue` / `ServerPrompts.vue`
  展示详情，权限审批和观测分别在 `permission/`、`observability/`。
- 提交时 `resource_names` 与 `tool_names` 按同一选择序列组装。回显、排序、删除和别名修改
  都要保留对应关系；Web 表单不要自行拼接代理数据库里的存储表示。
- 编辑使用 `patchServer`，创建使用 `createServer`；编辑提交只选择允许修改的字段。
  保留已有隐藏分类 ID，避免编辑表单未展示的分类被意外清除。
- `protocol_type`、`raw_response_enabled`、两个 OAuth2 客户端开关分别传输；
  不要由其中一个推断另一个。URL 预览由 `ServerBasicForm.vue` 结合服务名、前缀和协议生成。
- 工具/提示模板选择与基础表单校验都通过后才能提交；保留私有提示模板的确认流程。
  选择候选的环境改变后需检查候选刷新和旧选择回显。
- 观测页面使用 `src/services/source/mcp-server.ts` 等既有服务入口；日志、指标和 trace
  查询有不同参数与结果。修改表格/图表时检查时间范围、空结果、错误和分页行为。
- 相关页面验证包括新建、编辑回显、工具别名、协议切换、权限和观测中受影响的流程；
  不另复制组件级构建/类型检查命令。
