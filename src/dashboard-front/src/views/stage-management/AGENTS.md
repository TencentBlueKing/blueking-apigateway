# 环境管理

- `overview/Index.vue` 切换卡片/详情布局；两种布局共享环境状态。修改环境展示时同时检查
  `card-mode/` 与 `detail-mode/`，避免只更新一个入口。
- `detail-mode/components/` 分别处理环境变量、插件、已发布资源和资源详情。
  资源详情复用资源管理中的协议组件；修改共享组件时需核对环境中的只读展示。
- `overview/components/ReleaseProgrammable.vue` 和 `components/ReleaseProgrammableEvent.vue`
  处理可编程网关的部署及发布事件，不能用普通网关发布流程代替其 PaaS 部署状态。
- 普通发布的共享组件位于 `src/components/`；请求和事件类型见
  `src/services/source/release.ts`。修改发布逻辑需核对环境 ID、版本 ID、发布记录和数据面关联，
  避免把提交请求成功显示为最终发布成功。
- `release-record/Index.vue` 是历史查询入口；保留失败/进行中/超时等展示和事件详情。
  涉及轮询时检查页面切换、弹窗关闭及卸载后的停止逻辑。
- 页面验证按改动覆盖环境切换、两种布局、编辑后回显，以及发布成功/失败的受影响分支；
  不通过执行真实生产发布来验证纯展示改动。
