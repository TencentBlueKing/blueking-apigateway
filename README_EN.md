![img](docs/resource/img/blueking_apigateway_en.png)
---

[![license](https://img.shields.io/badge/license-MIT-brightgreen.svg?style=flat)](https://github.com/TencentBlueKing/blueking-apigateway/blob/main/LICENSE.txt) [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/TencentBlueKing/blueking-apigateway/pulls)

[简体中文](README.md) | English

## Overview

BlueKing API Gateway is a high-performance and highly available API hosting service that helps developers create, publish, maintain, monitor, and protect APIs, allowing for quick, low-cost, and low-risk access to data or services from BlueKing applications or other systems.

The BlueKing API Gateway is divided into the control plane and the data plane. The control plane is responsible for functions such as API configuration, publishing, monitoring, and permission management. The data plane handles API traffic forwarding, security protection, and other functions. The data plane is built on [Apache APISIX](https://github.com/apache/apisix) with a series of additional plugins to support the features of the BlueKing API Gateway. Thanks to the dynamic, real-time, and high-performance characteristics of Apache APISIX, the BlueKing API Gateway can support high-concurrency and low-latency API services.

This project is the "BlueKing API Gateway - Control Plane".

**BlueKing API Gateway Core Services Open Source Projects**

- BlueKing API Gateway - [Control Plane](https://github.com/TencentBlueKing/blueking-apigateway)
  - dashboard: Control plane for the API gateway
  - dashboard-front: Frontend for the API gateway control plane
  - core-api: Gateway high performance core API
  - esb: ESB component service
- BlueKing API Gateway - [Data Plane](https://github.com/TencentBlueKing/blueking-apigateway-apisix)
- BlueKing API Gateway - [Operator](https://github.com/TencentBlueKing/blueking-apigateway-operator)

## Features

- API lifecycle management: covering the management of API configuration, release, testing, monitoring, and deactivation throughout the entire lifecycle.
- Version release: supporting multi-environment management where users can create new environments to meet the needs of development, testing, and production; providing API version management where each environment can switch versions with just one click without affecting each other.
- Documentation and SDK: providing online documentation and an SDK for calling the gateway API, reducing the threshold for using the API.
- Authorization management: default authorization restrictions are enabled, supporting authorization expiration and authorization dimensions.
- Security protection: supporting BlueKing application authentication, user authentication, controlling the source of requests; supporting IP access control, where IP blacklist/whitelist can be set; supporting second-level traffic control, traffic allocation can be made according to demand, to avoid backend service overload caused by high traffic; supporting operation auditing.
- Observability: supporting call flow query; supporting integration with OpenTelemetry; built-in various alert strategies.

## Getting started

- [Local Developing(In Chinese)](docs/DEVELOP_GUIDE.md)

## Support

- [white paper(In Chinese)](https://bk.tencent.com/docs/document/7.0/171/13974)
- [bk forum](https://bk.tencent.com/s-mart/community)
- [bk DevOps online video tutorial(In Chinese)](https://bk.tencent.com/s-mart/video)
- Join technical exchange QQ group:

![img](docs/resource/img/bk_qq_group.png)

## BlueKing Community

- [BK-CI](https://github.com/TencentBlueKing/bk-ci): a continuous integration and continuous delivery system that can
  easily present your R & D process to you.
- [BK-BCS](https://github.com/TencentBlueKing/bk-bcs): a basic container service platform which provides orchestration
  and management for micro-service business.
- [BK-SOPS](https://github.com/TencentBlueKing/bk-sops): an lightweight scheduling SaaS for task flow scheduling and
  execution through a visual graphical interface.
- [BK-CMDB](https://github.com/TencentBlueKing/bk-cmdb): an enterprise-level configuration management platform for
  assets and applications.
- [BK-JOB](https://github.com/TencentBlueKing/bk-job): BlueKing JOB is a set of operation and maintenance script
  management platform with the ability to handle a large number of tasks concurrently.

## Contributing

If you have good ideas or suggestions, please let us know by Issues or Pull Requests and contribute to the Blue Whale
Open Source Community. For blueking-apigateway branch management, issues, and pr specifications, read
the [CONTRIBUTING(In Chinese)](docs/CONTRIBUTING.md)

If you are interested in contributing, check out the [CONTRIBUTING.md], also join
our [Tencent OpenSource Plan](https://opensource.tencent.com/contribution).


## Partners

<a href="https://apisix.apache.org/" target="_blank"><img src="https://github.com/apache/apisix/blob/master/logos/apisix-white-bg.jpg" alt="APISIX logo" height="150px" /></a>

## License

blueking-apigateway is based on the MIT protocol. Please refer to [LICENSE](LICENSE.txt)
