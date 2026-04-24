# Contract: BDD Case File Format

**Version**: 1.0
**Date**: 2026-03-30

## File Location

```
test/bdd-cases/<NN-模块名>/<NN-场景名>.md
```

Where:
- `NN` is a zero-padded sequence number (01, 02, ...)
- 模块名 is the Chinese module name (e.g., 网关管理, 资源配置)
- 场景名 is the Chinese scenario name (e.g., 创建普通网关)

## Format

```markdown
# 功能: [模块名] - [功能描述]

**模块**: [模块名]
**页面**: [URL path pattern]
**优先级**: P1|P2|P3
**前置条件**: [comma-separated prerequisites, e.g., 已登录, 测试网关已创建]

## 场景: [场景名称]

- **假设** [precondition/initial state]
- **当** [user action]
- **并且** [additional user action] (optional, repeatable)
- **那么** [expected outcome/verification]
- **并且** [additional verification] (optional, repeatable)

## 场景: [another scenario]

- **假设** ...
- **当** ...
- **那么** ...
```

## Rules

1. All text content MUST be in Chinese
2. Each file contains exactly one `# 功能` header
3. Each file contains 1-8 `## 场景` sections
4. Keywords: 功能, 场景, 假设, 当, 并且, 那么
5. `**页面**` uses parameterized paths (`:gatewayId` not literal IDs)
6. `**前置条件**` lists runtime dependencies (auth, test gateway, etc.)
7. Steps should describe user-visible actions, not implementation details

## Example

```markdown
# 功能: 网关管理 - 创建网关

**模块**: 网关管理
**页面**: /
**优先级**: P1
**前置条件**: 已登录

## 场景: 创建普通网关

- **假设** 用户在网关列表页
- **当** 点击"新建网关"按钮
- **并且** 选择网关类型为"普通网关"
- **并且** 输入网关名称、维护人员
- **并且** 选择"公开"
- **并且** 点击"提交"
- **那么** 网关创建成功
- **并且** 在网关列表中可以找到新创建的网关

## 场景: 创建网关时名称为空

- **假设** 用户在新建网关对话框中
- **当** 不填写网关名称
- **并且** 点击"提交"
- **那么** 显示名称不能为空的错误提示
```
