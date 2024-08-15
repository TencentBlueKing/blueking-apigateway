![img](docs/resource/img/blueking_apigateway_zh.png)
---

[![license](https://img.shields.io/badge/license-MIT-brightgreen.svg?style=flat)](https://github.com/TencentBlueKing/blueking-apigateway/blob/main/LICENSE.txt) [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/TencentBlueKing/blueking-apigateway/pulls)

简体中文 | [English](README_EN.md)

## 概览

蓝鲸 API 网关（API Gateway），是一种高性能、高可用的 API 托管服务，可以帮助开发者创建、发布、维护、监控和保护 API， 以快速、低成本、低风险地对外开放蓝鲸应用或其他系统的数据或服务。

蓝鲸 API 网关分为控制面和数据面，控制面负责 API 的配置、发布、监控、权限管理等功能，数据面负责 API 的流量转发、安全防护等功能。其中数据面是基于 [Apache APISIX](https://github.com/apache/apisix) 增加一系列插件以支持蓝鲸 API 网关的特性。得益于 Apache APISIX 动态、实时、高性能等特点，蓝鲸 API 网关能够支持高并发、低延迟的 API 托管服务。

本项目是 `蓝鲸 API 网关 - 控制面`。

**蓝鲸 API 网关核心服务开源项目**

- 蓝鲸 API 网关 - [控制面](https://github.com/TencentBlueKing/blueking-apigateway)
  - dashboard：API 网关的控制面
  - dashboard-front:  API 网关控制面前端
  - core-api: 网关高性能核心 API
  - esb: ESB 组件服务
- 蓝鲸 API 网关 - [数据面](https://github.com/TencentBlueKing/blueking-apigateway-apisix)
- 蓝鲸 API 网关 - [Operator](https://github.com/TencentBlueKing/blueking-apigateway-operator)

## 功能特性

- API 生命周期管理: 涵盖 API 的配置、发布、测试、监控、下线等各个生命周期的管理。
- 版本发布: 支持多环境管理，用户可新建环境，满足开发、测试、正式等多环境的需求;提供 API 的版本管理，各环境可一键切换版本，互不影响。
- 文档和SDK: 提供在线文档，及调用网关 API 的 SDK，降低 API 的使用门槛。
- 权限管理: 默认开启权限限制, 支持权限期限及授权维度。
- 安全防护: 支持蓝鲸应用认证、用户认证，控制请求来源; 支持 IP 访问控制，可设置 IP 黑/白名单; 支持秒级的流量控制，可根据需求进行流量分配，以避免高流量导致的后端服务过载; 支持操作审计。
- 可观测性: 支持调用流水查询; 支持接入 OpenTelemetry; 内置多种告警策略。

## 快速开始

- [本地开发部署指引](docs/DEVELOP_GUIDE.md)

## 支持

- [蓝鲸 API 网关产品白皮书](https://bk.tencent.com/docs/document/7.0/171/13974)
- [蓝鲸智云 - 学习社区](https://bk.tencent.com/s-mart/community)
- [蓝鲸 DevOps 在线视频教程](https://bk.tencent.com/s-mart/video)
- 加入技术交流 QQ 群：

![img](docs/resource/img/bk_qq_group.png)

## 蓝鲸社区

- [BK-CI](https://github.com/TencentBlueKing/bk-ci)：蓝鲸持续集成平台是一个开源的持续集成和持续交付系统，可以轻松将你的研发流程呈现到你面前。
- [BK-BCS](https://github.com/TencentBlueKing/bk-bcs)：蓝鲸容器管理平台是以容器技术为基础，为微服务业务提供编排管理的基础服务平台。
- [BK-SOPS](https://github.com/TencentBlueKing/bk-sops)：标准运维（SOPS）是通过可视化的图形界面进行任务流程编排和执行的系统，是蓝鲸体系中一款轻量级的调度编排类
  SaaS 产品。
- [BK-CMDB](https://github.com/TencentBlueKing/bk-cmdb)：蓝鲸配置平台是一个面向资产及应用的企业级配置管理平台。
- [BK-JOB](https://github.com/TencentBlueKing/bk-job)：蓝鲸作业平台（Job）是一套运维脚本管理系统，具备海量任务并发处理能力。

## 贡献

如果你有好的意见或建议，欢迎给我们提 Issues 或 PullRequests，为蓝鲸开源社区贡献力量。关于分支 / Issue 及 PR,
请查看 [CONTRIBUTING](docs/CONTRIBUTING.md)。

[腾讯开源激励计划](https://opensource.tencent.com/contribution) 鼓励开发者的参与和贡献，期待你的加入。

## 合作方

<a href="https://apisix.apache.org/" target="_blank"><img src="https://github.com/apache/apisix/blob/master/logos/apisix-white-bg.jpg" alt="APISIX logo" height="150px" /></a>

## 证书

基于 MIT 协议，详细请参考 [LICENSE](LICENSE.txt)