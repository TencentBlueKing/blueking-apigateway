# Dashboard Frontend

## 运行与验证

所有命令在 `src/dashboard-front` 执行。技术栈为 Vue 3、TypeScript、Vite、Pinia，
以 `package.json` 和锁文件为版本依据，不在本文件维护依赖版本副本。
Node 要求见 `package.json.engines`；CI 和 Docker 当前使用 24.15.0。
优先用 pnpm，缺少时使用对应的 `npm run`；不要因切换包管理器产生无关锁文件更新。

| 命令 | 用途 |
| --- | --- |
| `pnpm dev` | 开发服务，端口 8888，使用 basic SSL 插件 |
| `pnpm dev:tenant` | 以 tenant mode 启动，环境文件遵循 Vite 的 `.env.tenant` / `.env.tenant.local` 命名 |
| `pnpm build` | 类型检查和生产构建 |
| `pnpm build-only` | 仅打包，不能代替类型检查 |
| `pnpm type-check` | `vue-tsc --build` |
| `pnpm lint:ci` | ESLint 检查，不自动修复 |
| `pnpm lint:eslint` | ESLint 自动修复，执行后检查 diff |
| `pnpm preview` | 本地预览构建产物 |

代码改动执行 `pnpm type-check`、`pnpm lint:ci`；构建配置或依赖改动还需验证构建。
`.github/workflows/dashboard-front.yml` 实际运行类型检查和 ESLint，Docker 使用
`npm run build`。若有失败，保留证据并区分既有问题，不能预设类型检查不可用。
本组件未配置自动测试脚本；交互变更需针对受影响页面验证，仓库级 BDD 入口见根指引。

## 代码入口与约束

- `src/main.ts` 安装插件、指令和全局组件；`src/App.vue` 负责导航及用户/环境信息。
- `src/router/index.ts` 组合视图目录的 `route.ts` / `routes.ts`，使用
  `createWebHistory(window.BK_SITE_PATH)`。从实际路由生成链接，避免将目录名当 URL。
- `src/router/gateway-role-guard.ts`、`src/stores/useGatewayRole.ts` 和
  `src/utils/gateway-permission.ts` 控制成员角色与页面访问。新增路由/操作需检查权限元数据、
  菜单和按钮控制；网关详情仅用于展示，不能替代角色授权。守卫直接导入具体 Store 以避免循环依赖。
- `src/stores/index.ts` 是普通消费者的 Store 导出入口；`useGateway` 保存当前网关，
  `useEnv` 保存环境配置，`useFeatureFlag` 控制功能显隐。跨网关切换注意异步请求和缓存归属。
- API 函数集中在 `src/services/source/`，复用 `src/services/http/`。
  `http/lib/request.ts` 负责 CSRF、取消和 GET 缓存；`payload.permission` 选择
  `page` / `dialog` / `catch` 错误展示策略。不要在页面另建 Axios 客户端。
- `src/components/` 提供通用组件和插件表单，`src/hooks/` 提供组合式逻辑。
  UI 优先使用 bkui-vue，高级表格按现有 TDesign 封装模式实现。
- `src/locales/{cn,en}.json` 同步维护用户可见文本，通常以中文文本为 key；
  语言由 `blueking_language` Cookie 决定，默认 `zh-cn`。使用既有 `t` / `useI18n`。

## 本地规范与工具

修改 TS/Vue 时读取 `.agents/rules/ts-style.md` 和 `.agents/rules/vue-code-style.md`。
实际格式和校验规则由 `eslint.config.ts`、`stylelint.config.js` 管理，不复制规则表或模板代码。
其中 Vue/TS 规范要求类型化 Props/Emits、响应式 Props 解构、接口 `I` 前缀；
ESLint 另约束宏顺序及 `defineExpose` 位置。以目标文件和生效配置核对示例。

按具体任务读取本组件 `.agents/skills/` 中的技能，不预加载全部技能：

| 技能 | 场景 |
| --- | --- |
| `bkui-builder` / `bkui-cheatsheet` | 设计稿、布局与 BKUI 组件 |
| `api-standard` | API 请求封装 |
| `pinia-setup` | 状态管理 |
| `i18n-maintainer` | 国际化维护 |

`vite.config.ts` 配置 Vue、Vue Router 和 `useI18n` 自动导入，生成
`src/types/auto-imports.d.ts`。`@` 对应 `src/`，同时定义在 Vite 和
`tsconfig.app.json`；`bkui-lib` 是 Vite 中的兼容别名，不要声称它已配置在 TS paths 中。
`bk-user-display-name` 和 `status-tag` 是自定义元素。

样式使用 SCSS 和 UnoCSS；构建时 `VITE_*` 与运行时 `window.BK_*` 配置职责不同。
`index.dev.html` / `index.prod.html` 经 `replace-index-html.js` 选择，部署运行变量还需
检查 `bin/`。图标字体目录 `src/assets/bk_icon_font` 不属于常规分析/修改范围。

提交规范见 `.commitlintrc.cjs`。已安装的 simple-git-hooks 会在提交前运行
lint-staged（可改写暂存代码）和类型检查；不要将钩子存在视为已经执行验证。
