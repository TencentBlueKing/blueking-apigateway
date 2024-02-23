<!-- 2024-02-21 -->
# V1.13.0 版本更新日志

### 缺陷修复

### 功能优化

- 重构后端代码，协议规范化
- 全新的产品页面

---

<!-- 2024-01-24 -->
# V1.12.16 版本更新日志

### 缺陷修复

- 修复 esb 组件无法同步成功的问题(升级esb到2.14.65)
- 隐藏 bk-header-rewrite 插件配置

### 功能优化

- 升级 bk-esb 到 2.14.64, 包含监控和bklog的变更
- 增加校验: gateway_name/stage_name/resource_name 不允许以 `-` 和 `_` 结尾

---

<!-- 2023-12-28 -->
# V1.12.14 版本更新日志

### 缺陷修复

- 修复 检测 resource_perm_required 之前，先检查 verified_app_required = True
- open api 中 sync stage 不触发发布，允许网关的环境中变量不存在

### 功能优化

- 升级 esb 到 2.14.61
- 查询应用已有权限时，允许展示正在申请中的权限状态
- 检查应用访问网关资源的权限，如果快过期则发送通知给应用负责人
- 告警信息中，去掉querystring
- 统计: 支持按网关拉取请求量数据

---

<!-- 2023-11-08 -->
# V1.12.9 版本更新日志

### 缺陷修复

- 修复: PluginConfigManager missing method bulk_delete
- 修复: operator diff 不生效
- 修复： apisix dns 解析失败无法恢复问题

### 功能优化

- api文档增加 bk_token 说明
- apisix 支持 graceful shutdown
- apisix rebuild radixtree 优化
- 网关支持配置开发者

---

<!-- 2023-09-25 -->
# V1.12.1 版本更新日志

> 正式外发版本

### 缺陷修复

- 修复: operator 去重 bug
- 修复: operator 全量同步 bug
- 修复: apisix 线上问题
- 修复: 前端交互问题
- 修复： 请求后端接口异常时，不对结果进行缓存

### 功能优化

- 支持配置 externalRabbitmq
