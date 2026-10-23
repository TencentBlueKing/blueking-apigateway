# 蓝鲸 API Gateway



## 推荐的包管理器

`pnpm`

## Node.js 版本

使用 Node.js 24 LTS，最低版本为 `24.22.1`。`.nvmrc`、Docker 构建和 CI 当前统一使用 `24.22.1`。

使用 nvm 的开发环境可在本目录执行 `nvm install` 和 `nvm use`；nvm-windows 需执行 `nvm install 24.22.1` 和 `nvm use 24.22.1`。

## 如何让`.agents`可被 codybuddy 使用

- 如果你是初次部署本项目，那么在安装完依赖后，`.agents`会被自动创建一个名为`.codebuddy`的软链接，里面的配置可被 codybuddy 使用


- 如果要手动创建软链接，那么你需要执行`symlink-dot-agents:codebuddy`脚本：

```pnpm symlink-dot-agents:codebuddy```


