# 蓝鲸 API Gateway



## 推荐的包管理器

`pnpm`

## 如何让`.agents`可被 codybuddy 使用

- 如果你是初次部署本项目，那么在安装完依赖后，`.agents`会被自动创建一个名为`.codebuddy`的软链接，里面的配置可被 codybuddy 使用


- 如果要手动创建软链接，那么你需要执行`symlink-dot-agents:codebuddy`脚本：

```pnpm symlink-dot-agents:codebuddy```


