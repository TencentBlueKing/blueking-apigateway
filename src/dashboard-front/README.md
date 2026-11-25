# 蓝鲸 API Gateway



## 推荐的包管理器

`pnpm`

## Node.js 版本

使用 Node.js 24 LTS，最低版本为 `24.22.1`。`.nvmrc`、Docker 构建和 CI 当前统一使用 `24.22.1`。

使用 nvm 的开发环境可在本目录执行 `nvm install` 和 `nvm use`；nvm-windows 需执行 `nvm install 24.22.1` 和 `nvm use 24.22.1`。

## 如何让`.agents`可被 codybuddy 使用

- 如果你是初次部署本项目，那么在安装完依赖后，`.agents`会被自动创建一个名为`.codebuddy`的软链接，里面的配置可被 codybuddy 使用


- 如果要手动创建软链接，那么你需要执行`symlink-dot-agents:codebuddy`脚本：

```bash
pnpm symlink-dot-agents:codebuddy
```

## 推荐安装的 Vue Agent Skills（可选）

推荐开发者及其 AI Agents 在本机按需安装 [vuejs-ai/skills](https://github.com/vuejs-ai/skills) 中的 Vue 3 相关技能（非强制，仅作最佳实践与调试参考）：

```bash
npx skills add vuejs-ai/skills
```

- 建议按需选用：`vue-best-practices`、`vue-pinia-best-practices`、`vue-router-best-practices`、`vue-testing-best-practices`、`vue-jsx-best-practices`、`vue-debug-guides`、`create-adaptable-composable`。
- 若与本仓规范存在差异，以本目录 [AGENTS.md](./AGENTS.md) 与 `.agents/rules/` 中的本地约定为准。


