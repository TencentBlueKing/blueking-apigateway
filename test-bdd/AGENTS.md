# BDD Test Suite - Business Context

> This file contains domain-specific knowledge for the BlueKing API Gateway BDD test suite.
> It supplements the `bdd-test-gen` SKILL (`.agents/skills/bdd-test-gen/SKILL.md`) with
> information that is too detailed or volatile to include in the SKILL itself.

## Module Classification

The BDD test suite covers 26 functional modules organized under 5 top-level navigation sections:

### 我的网关 (Gateway Management)

| # | Module | Page Path | Type | Notes |
|---|--------|-----------|------|-------|
| 01 | 网关管理 | `/` | Mutating | CRUD gateways — use test gateway for create/delete |
| 02 | 资源配置 | `/:gatewayId/resources` | Mutating | CRUD resources, plugins, import/export |
| 03 | 资源版本 | `/:gatewayId/resource/version` | Mutating | Version generation requires resource changes first |
| 04 | SDK列表 | `/:gatewayId/sdk` | Read-only | View/filter SDK list |
| 05 | 环境概览 | `/:gatewayId/stage/overview` | Mutating | Publish/unpublish resources to stages |
| 06 | 环境资源信息 | `/:gatewayId/stage/resource` | Read-only | View resources by environment |
| 07 | 环境插件管理 | `/:gatewayId/stage/plugin` | Mutating | CRUD environment-level plugins |
| 08 | 环境变量管理 | `/:gatewayId/stage/variable` | Mutating | CRUD stage variables |
| 09 | 发布记录 | `/:gatewayId/release/history` | Read-only | View release history |
| 10 | 后端服务 | `/:gatewayId/backends` | Mutating | CRUD backend services — must configure before resource creation |
| 11 | 权限审批 | `/:gatewayId/permission/applys` | Mutating | Approve/reject permission requests |
| 12 | 应用权限 | `/:gatewayId/permission/apps` | Read-only | View app permission records |
| 13 | 访问日志 | `/:gatewayId/access-log` | Read-only | View/search access logs |
| 14 | 统计报表 | `/:gatewayId/statistics` | Read-only | View statistics charts |
| 15 | 在线调试 | `/:gatewayId/online-debug` | Mutating | Send debug requests |
| 16 | 调试历史 | `/:gatewayId/online-debug/history` | Read-only | View debug request history |
| 17 | 基本信息 | `/:gatewayId/basic-info` | Mutating | View/edit gateway settings, deactivate/delete |
| 18 | MCP服务 | `/:gatewayId/mcp` | Mutating | CRUD MCP Servers |
| 19 | MCP权限审批 | `/:gatewayId/mcp/permission` | Mutating | Approve/reject MCP permissions |
| 20 | 操作记录 | `/:gatewayId/audit` | Read-only | View operation audit logs |

### 组件管理 (Component Management)

| # | Module | Page Path | Type |
|---|--------|-----------|------|
| 21 | 组件管理 | `/components/access` | Mutating |
| 22 | 文档分类 | `/components/doc-category` | Mutating |
| 23 | 实时运行数据 | `/components/realtime` | Read-only |

### API 文档 (API Documentation)

| # | Module | Page Path | Type |
|---|--------|-----------|------|
| 24 | API文档 | `/docs/api-docs` | Read-only |

### 平台工具 (Platform Tools)

| # | Module | Page Path | Type |
|---|--------|-----------|------|
| 25 | 平台工具 | `/tools` | Read-only |

### MCP 市场 (MCP Market)

| # | Module | Page Path | Type |
|---|--------|-----------|------|
| 26 | MCP市场 | `/mcp-market` | Read-only |

## Recommended Execution Order

1. **Setup**: Create test gateway, configure backend, create resource, publish
2. **Read-only modules first**: 04, 06, 09, 12, 13, 14, 16, 20, 23, 24, 25, 26
3. **Resource lifecycle**: 02 → 03 → 05
4. **Environment config**: 07, 08
5. **Backend services**: 10
6. **Permission flows**: 11, 19
7. **MCP Server**: 18
8. **Online debug**: 15
9. **Basic info**: 17 (last — may deactivate gateway)
10. **Teardown**: Delete test gateway

## Domain Gotchas

### Login
- Chinese form: `input[placeholder="请输入用户名"]` / `input[placeholder="请输入密码"]` / `立即登录`
- Session expiry redirects to `/login/`

### BkSelect Dropdowns
- **NEVER use `Escape`** — causes toggle bug. Dismiss with `body.click({ position: { x: 10, y: 10 } })`

### Gateway Operations
- Name: lowercase letters, numbers, hyphens; starts with lowercase; 3-30 chars
- Deletion: deactivate (停用) → delete (删除) → may require typing name

### Resource Operations
- Backend service **must be configured first** (error: "后端服务地址不允许为空")
- Version generation disabled when no resource changes

### Publish Flow
- "生成版本" → "下一步" → "确定" → "立即发布" → select stage → "下一步" → "确认发布" → InfoBox confirm
