# 1.26 组件管理下线升级说明

后端 PR [#3417](https://github.com/TencentBlueKing/blueking-apigateway/pull/3417)
必须与前端 PR [#3415](https://github.com/TencentBlueKing/blueking-apigateway/pull/3415)
同一版本发布，不支持仅升级后端并继续使用旧版前端。旧前端的组件管理深链接仍可能请求已删除的
`/backend/esb/` 管理接口并收到 404。

本次下线组件管理页面及其管理 API，包括页面触发的同步和发布入口。保留 ESB 数据库模型、迁移、
部署时的 `bk-esb` 网关注册、资源同步、发布命令与 Celery 任务，以及 Open/Inner 接口、组件文档和 SDK。
原有 ESB 开关和数据库、Celery 配置仍需保留；移除管理页面不等于停用存量 ESB 服务。

以下环境变量已不再被 Dashboard 读取，升级时可从部署配置中移除：

- `FEATURE_FLAG_MENU_ITEM_ESB_API`
- `FEATURE_FLAG_MENU_ITEM_ESB_API_DOC`
- `FEATURE_FLAG_SYNC_ESB_TO_APIGW_ENABLED`
- `DOC_LINK_COMPONENT_RATE_LIMIT`
- `DOC_LINK_COMPONENT_CREATE_API`
- `BK_ESB_API_LOG_ES_INDEX`

其中 `FEATURE_FLAG_SYNC_ESB_TO_APIGW_ENABLED` 原先仅控制前端能力展示，不控制后台同步。
`BK_ESB_API_LOG_ES_INDEX` 原先仅供组件管理运行数据页查询使用。
Helm chart 和 helm-values 中的残留配置需在各自仓库清理；TE 仓库中已不再被引用的空
`editions/te/apps/esb/urls.py` 也可另行删除。

本次不迁移或删除存量 `UserFeatureFlag` 数据。已保存的用户级旧 flag 仍可能出现在 feature flag
响应中，配套前端已移除其消费入口；这些值不会重新启用管理接口。

验证边界：启动回归覆盖路由解析、应用和数据库注册、任务模块导入、同步命令加载与部署脚本的命令分发。
同步命令、资源同步和发布逻辑另有单元测试。EE 和 TE 单测需分别激活各自 overlay；启动测试根据
`editionctl` 记录的实际版本检查对应命令，修改 `EDITION` 环境变量不会切换源代码。
上述检查不等同于真实部署或历史环境升级；EE 已有发布记录时，部署触发的后台同步还需由 Celery 完成，
命令返回不代表发布已完成。
