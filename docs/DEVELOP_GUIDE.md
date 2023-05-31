# 本地开发环境搭建

本地开发时，你可以根据需要，为实际开发的模块（dashboard / dashboard-front / core-api / esb）准备开发环境。

在开始开发前，你需要为整个项目安装并初始化 `pre-commit`，

```bash
# 假设你当前在项目的根目录下

❯ pre-commit install
```

## dashboard

`dashboard` 基于 Django 框架开发，为网关产品提供后端接口。本地开发环境搭建请参考 [本地开发文档](../src/dashboard/README.md)

## dashboard-front

`dashboard-front` 为基于 Vue.js 的前端项目。本地开发环境搭建请参考 [本地开发文档](../src/dashboard-front/README.md)

## core-api

`core-api` 是基于 Gin 框架开发的接口服务, 为 APISIX 插件及 OpenAPI 提供接口。本地开发环境搭建请参考 [本地开发文档](../src/core-api/README.md)

## esb

`esb` 为基于 Python 的内部 ESB 框架, 用于支持企业级组件。本地开发环境搭建请参考 [本地开发文档](../src/esb/README.md)
