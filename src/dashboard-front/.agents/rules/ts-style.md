---
# 注意不要修改本文头文件，如修改，CodeBuddy（内网版）将按照默认逻辑设置
type: always
---
# TypeScript 编码规范

## 基本原则

- `interface` 声明的类型**必须**以大写字母 `I` 开头，如 `IProps`、`IEmits`、`IGatewayDetail`、`ITableColumn` 等。
- 联合类型、交叉类型、映射类型或函数签名别名使用 `type`（如 `type GatewayRoleStatus = 'idle' | 'loading' | 'ready' | 'error'`）。
- 仅用于类型标注的导入优先使用 `import type`（或内联 `type` 修饰符），避免引入多余的运行时依赖。
- 尽管 ESLint 为兼容存量代码关闭了 `@typescript-eslint/no-explicit-any`，新增与重构代码仍应避免使用 `any`，优先复用 `src/services/types/` DTO、泛型或 `unknown` 收窄。
