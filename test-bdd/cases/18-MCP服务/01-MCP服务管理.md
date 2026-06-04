# 功能: MCP服务 - MCP Server管理

**模块**: MCP服务
**页面**: /gateways/:id/mcp/server
**优先级**: P1
**前置条件**: 已登录，且存在已发布的资源

## 场景: MCP Server 生命周期

- **假设** 用户已登录并进入MCP Server页面
- **当** 用户创建唯一 MCP Server
- **并且** 编辑展示名和描述
- **并且** 停用后再次启用
- **并且** 删除 MCP Server
- **那么** `/mcp-servers/` 和 `/<id>/status/` 接口返回与操作一致
