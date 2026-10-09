# 资源管理

- `settings/edit/Index.vue` 组装提交请求，`Standard.vue` / `ModelProxy.vue` 分别处理普通和
  AI 资源表单。创建、编辑、克隆共用入口；修改时同时检查路由参数和 `kind`，不能只看网关类别。
- 请求/响应参数编辑器位于 `components/request-params-v2/`、`components/response-params-v2/`，
  各自 `utils.ts` 负责表格、JSON 与协议数据转换。变更需检查嵌套对象/数组、空值、媒体类型和
  编辑后回显，不能只验证表格外观。
- 编辑页将请求体写为 API 字段 `openapi_schema.request_body`，编辑器内部使用 `requestBody`；
  `none_schema` 表示无协议数据。更新已有资源时还要保留协议版本；以实际组包分支为准。
- `settings/import/` 的预览、选择和提交是不同阶段；路由冲突展示使用
  `components/ResourcePathConflictTips.vue`，不能将预检结果当成已保存。
- `versions/` 管理版本、文档和 SDK 展示。版本详情与 `settings/` 草稿编辑使用不同 API；
  SDK 信息复用 `src/services/source/` 返回值，避免在视图自行拼接包名或地址。
- 涉及上述路径时，页面验证覆盖新增、编辑、克隆/导入中的受影响流程，以及保存后重新打开；
  通用验证命令沿用组件指引。
