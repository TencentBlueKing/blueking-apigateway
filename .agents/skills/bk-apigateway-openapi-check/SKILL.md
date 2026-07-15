---
name: bk-apigateway-openapi-check
description: "仅限用户显式调用的 API 一致性检查技能。只有当用户明确要求调用或使用 `bk-apigateway-openapi-check` 时才使用；仅提及、编辑或评审该技能，以及任务涉及 API、OpenAPI、YAML、API 文档或一致性检查，均不得触发本技能。"
---

TRIGGER RULE: 本技能禁止主动调用。只有用户在当前请求中明确要求调用或使用 `bk-apigateway-openapi-check` 时，才进入下方工作流。仅提及、编辑或评审本技能不算授权；OpenAPI、API、YAML、文档相关任务以及常规 lint、test、preflight 也不算授权。

IRON LAW: 检查操作均为只读，禁止直接修改 YAML 资源定义或代码路由。`--fix` 仅允许生成文档模板。每条检查结果必须包含具体的 operationId 和问题描述，禁止输出模糊结论。

Red Flags（立即停止并回退）：
- 用户要求直接修改 YAML 或代码路由而未经过评审确认
- 将 WARNING 误报为 ERROR 导致恐慌性修改
- 忽略已知特殊 case（见 [references/special-cases.md](references/special-cases.md)）而强行报告为错误

## Workflow Checklist

- [ ] Step 1: 确认检查范围 ⚠️ REQUIRED
  - [ ] 1.1 确认 scope（`all` / `v2_open` / `v2_inner` / `v2_sync`）
  - [ ] 1.2 确认项目路径（默认自动探测）
  - [ ] 1.3 确认是否需要 `--fix`（仅生成缺失文档模板）
- [ ] Step 2: 运行检查脚本 ⛔ BLOCKING
  - [ ] 2.1 `python scripts/check_api_consistency.py --scope <SCOPE>`
  - [ ] 2.2 如需机器可读输出，加 `--json`
  - [ ] 2.3 如需检查单个 API，加 `--api <OPERATION_ID>`
- [ ] Step 3: 解读报告 ⚠️ REQUIRED
  - [ ] 3.1 ERROR 必须修复（会导致运行时错误或权限问题）
  - [ ] 3.2 WARNING 建议修复（不会导致功能故障）
  - [ ] 3.3 按 P0→P3 优先级处理（详见 [references/check-criteria.md](references/check-criteria.md)）
- [ ] Step 4: 自动修复（如指定 `--fix`）⚠️ REQUIRED 确认
  - [ ] 4.1 向用户展示缺失文档清单
  - [ ] 4.2 获取明确确认后执行（仅生成 Markdown 模板）
  - [ ] 4.3 提醒用户人工补充详细内容
- [ ] Step 5: 交付检查报告

## 工具速查

| 需求 | 命令 |
|------|------|
| 检查全部 | `python scripts/check_api_consistency.py` |
| 按范围检查 | `python scripts/check_api_consistency.py --scope v2_sync` |
| 检查单个 API | `python scripts/check_api_consistency.py --api v2_sync_gateway` |
| JSON 输出 | `python scripts/check_api_consistency.py --json` |
| 生成缺失文档 | `python scripts/check_api_consistency.py --fix` |
| 指定项目路径 | `python scripts/check_api_consistency.py --project-dir /path/to/project` |

## Scope 说明

| scope | YAML tags | 代码目录 | 说明 |
|-------|-----------|----------|------|
| `all` | 全部 | 全部 | 默认 |
| `v2_open` | `v2`+`open` | `apis/v2/open/` | 开放 API |
| `v2_inner` | `v2`+`inner` | `apis/v2/inner/` | 内部 API |
| `v2_sync` | `v2`+`sync` | `apis/v2/sync/` | 同步 API |

## 三层关系

```
operationId (唯一标识)
  ├── YAML: bk-apigateway-resources.yaml → paths[path][method].operationId
  ├── 代码: urls.py → views.py → serializers.py
  └── 文档: apidocs/zh/{operationId}.md
```

详细文件引用和路径映射见 [references/file-reference.md](references/file-reference.md)。

## 检查项概览

| # | 检查项 | 核心关注点 |
|---|--------|-----------|
| CHECK-1 | 存在性 | 三层都有定义 |
| CHECK-2 | 路径一致性 | YAML path ↔ 代码 URL ↔ backend.path |
| CHECK-3 | HTTP 方法 | YAML method ↔ View method |
| CHECK-4 | 请求参数 | YAML parameters ↔ Serializer 字段 ↔ 文档 |
| CHECK-5 | 响应参数 | YAML response ↔ Serializer 输出 ↔ 文档 |
| CHECK-6 | 鉴权配置 | isPublic / authConfig ↔ permission_classes |
| CHECK-7 | grant_permissions | 授权的资源是否存在 |
| CHECK-8 | MCP Server | resource_names 是否存在，数量是否匹配 |

每项检查的详细判定规则和严重度见 [references/check-criteria.md](references/check-criteria.md)。

已知特殊 case 见 [references/special-cases.md](references/special-cases.md)。

## 确认门控

### 修复前确认 ⚠️ REQUIRED

执行 `--fix` 前，向用户展示：缺失文档清单 → 修复策略（仅生成模板）→ 影响范围（新增文件列表）。获取明确确认后执行。

## Anti-Patterns

- 禁止直接修改 YAML 或代码 — 检查工具为只读，修复由人工确认后执行
- 禁止对 core-api / mcp-proxy backend 报告代码缺失 — 后端不指向 dashboard
- 禁止混淆 WARNING 和 ERROR — WARNING 不导致功能故障
- 禁止遗漏特殊 case — 见 [references/special-cases.md](references/special-cases.md)
- 禁止输出模糊结论 — 每条结果必须包含 operationId 和问题描述
- 禁止在生产环境运行 `--fix` — 仅在本地开发环境执行

## Pre-Delivery Checklist

- [ ] 检查脚本运行成功并输出完整报告
- [ ] ERROR / WARNING 已按 P0-P3 分类
- [ ] 每条结果包含具体 operationId 和文件路径
- [ ] 已知特殊 case 已正确跳过
- [ ] `--fix` 已获用户确认且仅生成文档模板
- [ ] 报告包含摘要统计（总数/通过/错误/警告）

## 相关资源

### scripts/
- `scripts/check_api_consistency.py` — 主检查脚本

### references/
- `references/check-criteria.md` — CHECK-1~8 详细判定规则与严重度
- `references/file-reference.md` — 关键文件路径与三层映射关系
- `references/special-cases.md` — 已知特殊 case 白名单

---

**技能版本**: 1.1.0
**最后更新**: 2026-05-15
