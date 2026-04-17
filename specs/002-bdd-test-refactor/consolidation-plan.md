# Excel Analysis & Consolidation Plan

**Date**: 2026-03-30
**Source**: 蓝鲸API网关测试用例.xlsx (835 cases, 31 modules)

## Module Distribution

| # | Excel Module | Cases | Core Scenarios | BDD Directory | Strategy |
|---|-------------|-------|----------------|---------------|----------|
| 01 | 我的网关 | 42 | 5 | 01-网关管理 | CRUD gateway + name validation + type selection |
| 02 | 资源配置 | 235 | 8 | 02-资源配置 | CRUD resource + tags + plugins (merge 100+ plugin edge cases) |
| 03 | 资源版本 | 43 | 4 | 03-资源版本 | Generate/view/compare/diff versions |
| 04 | SDK列表 | 25 | 2 | 04-SDK列表 | View/filter SDKs |
| 05 | 环境概览 | 9 | 3 | 05-环境概览 | View overview + publish/unpublish |
| 06 | 环境资源信息 | 19 | 3 | 06-环境资源信息 | View/filter/detail |
| 07 | 环境插件管理 | 29 | 4 | 07-环境插件管理 | CRUD env plugins |
| 08 | 环境变量管理 | 3 | 2 | 08-环境变量管理 | CRUD env variables |
| 09 | 发布记录 | 15 | 2 | 09-发布记录 | View/filter records |
| 10 | 后端服务 | 27 | 4 | 10-后端服务 | CRUD backend services |
| 11 | 权限审批 | 18 | 3 | 11-权限审批 | List/approve/reject |
| 12 | 应用权限 | 33 | 3 | 12-应用权限 | View/manage/filter |
| 13 | 访问日志 | 10 | 2 | 13-访问日志 | View/search logs |
| 14 | 统计报表 | 12 | 2 | 14-统计报表 | View charts/time range |
| 15 | 在线调试 | 10 | 3 | 15-在线调试 | Send request/view response/config |
| 16 | 调试历史 | 19 | 2 | 16-调试历史 | View/filter history |
| 17 | 基本信息 | 18 | 3 | 17-基本信息 | View/edit/status |
| 18 | MCP服务 | 82 | 5 | 18-MCP服务 | CRUD MCP servers + config |
| 19 | MCP权限审批 | 12 | 2 | 19-MCP权限审批 | Approve/reject |
| 20 | 操作记录 | 25 | 2 | 20-操作记录 | View/filter records |
| 21 | 组件管理(简介+系统+组件) | 61 | 4 | 21-组件管理 | Merge 21/22/23: View/CRUD components+systems |
| 24 | 文档分类 | 17 | 2 | 22-文档分类 | Edit/manage categories |
| 25 | 实时运行数据 | 2 | 1 | 23-实时运行数据 | View realtime data |
| 26+27 | API文档(网关+组件) | 40 | 3 | 24-API文档 | Merge: Search/view gateway+component docs |
| 28+29+30 | 平台工具 | 10 | 2 | 25-平台工具 | Merge: Toolbox + auto gateway + programmable |
| 31 | MCP市场 | 19 | 2 | 26-MCP市场 | Browse/filter MCP market |

## Summary

- **Total original cases**: 835
- **Total BDD modules**: 26 (merged from 31 Excel modules)
- **Target BDD scenarios**: ~77 core scenarios
- **Scenarios per module**: 1-8 (avg ~3)

## Consolidation Principles Applied

1. **Merged small related modules**: 21+22+23 → 组件管理, 26+27 → API文档, 28+29+30 → 平台工具
2. **Focused on core workflows**: CRUD paths per module, not edge case variations
3. **Validation folded in**: Name validation, empty fields etc. folded into create/edit scenarios
4. **Plugin edge cases compressed**: 100+ resource plugin cases → 2-3 plugin scenarios in 资源配置
5. **P1/P2 only**: P3 edge cases removed unless uniquely valuable
