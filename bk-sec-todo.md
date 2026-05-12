# BK Security Tickets Todo

| 项目 | 处理方式 | 工单 | 工单链接 | 库 | 建议升级版本 | 建议处理 | 原因 |
|---|---|---|---|---|---|---|---|
| `src/dashboard` | 待处理 | W202605121455121384303 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384300?from=myTodo&project_id=1) | idna | >=3.7 | 升级 | 支持 Python 3.10 |
| `src/dashboard` | 已忽略 | W202605121455121384304 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384301?from=myTodo&project_id=1) | markdown | >=3.8.1 | 不升 | 只在 lock 的 extra 中出现，不是实际安装包 |
| `src/dashboard` | 已忽略 | W202605121455121384300 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384297?from=myTodo&project_id=1) | grpcio | >=1.53.2 | 不升 | 已按反馈标记忽略 |
| `src/dashboard` | 待处理 | W202605121455121384307 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384304?from=myTodo&project_id=1) | pillow | >=12.2.0 | 升级 | 支持 Python 3.10 |
| `src/dashboard` | 已忽略 | W202605121455111384289 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384286?from=myTodo&project_id=1) | django | >=4.2.26 | 不升 | 当前明确不能升级 Django，项目固定 Django 3.2 |
| `src/dashboard` | 待处理 | W202605121455111384283 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384280?from=myTodo&project_id=1) | cryptography | >=46.0.6 | 升级 | 支持 Python 3.10 |
| `src/dashboard` | 待处理 | W202605121455111384285 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384282?from=myTodo&project_id=1) | certifi | >=2024.7.4 | 升级 | 兼容当前环境 |
| `src/dashboard` | 待处理 | W202605121424141384132 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384129?from=myTodo&project_id=1) | protobuf | >=5.29.6 | 不单独升 | 当前 opentelemetry-proto 要求 protobuf <5 |
| `src/dashboard` | 待处理 | W202605121424151384139 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384136?from=myTodo&project_id=1) | werkzeug | >=3.1.6 | 升级 | 支持 Python 3.10 |
| `src/dashboard` | 待处理 | W202605121424141384122 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384119?from=myTodo&project_id=1) | sqlparse | >=0.5.4 | 升级 | 支持 Python 3.10 |
| `src/dashboard` | 待处理 | W202605121424141384123 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384120?from=myTodo&project_id=1) | urllib3 | >=2.6.3 | 升级 | 支持 Python 3.10 |
| `src/dashboard` | 待处理 | W202605121424141384120 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384117?from=myTodo&project_id=1) | setuptools | >=78.1.1 | 升级 | 支持 Python 3.10 |
| `src/esb` | 待处理 | W202605121455121384303 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384300?from=myTodo&project_id=1) | idna | >=3.7 | 升级 | 支持 Python 3.6 |
| `src/esb` | 已忽略 | W202605121455121384304 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384301?from=myTodo&project_id=1) | markdown | >=3.8.1 | 不升 | 建议版本要求 Python >=3.9，ESB 固定 Python 3.6 |
| `src/esb` | 已忽略 | W202605121455121384297 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384294?from=myTodo&project_id=1) | gunicorn | >=22.0.0 | 不升 | ESB 镜像 Python 3.6，建议版本要求更高运行时 |
| `src/esb` | 已忽略 | W202605121455111384289 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384286?from=myTodo&project_id=1) | django | >=4.2.26 | 不升 | ESB 固定 Django 1.11，且不能升级 Django |
| `src/esb` | 已忽略 | W202605121455111384283 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384280?from=myTodo&project_id=1) | cryptography | >=46.0.6 | 不升 | 建议版本要求 Python >=3.8 |
| `src/esb` | 待处理 | W202605121455111384285 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384282?from=myTodo&project_id=1) | certifi | >=2024.7.4 | 升级 | 支持 Python 3.6 |
| `src/esb` | 待处理 | W202605121424141384116 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384113?from=myTodo&project_id=1) | pg8000 | >=1.31.5 | 不升 | PostgreSQL optional extra，项目实际使用 MySQL |
| `src/core-api` | 已处理 | W202605121455121384298 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384295?from=myTodo&project_id=1) | google.golang.org/grpc | >=1.79.3 | 升级 | 已升到 v1.80.0；OpenTelemetry exporter 要求 grpc v1.80.0 |
| `src/core-api` | 已处理 | W202605121455121384293 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384290?from=myTodo&project_id=1) | go.opentelemetry.io/otel/sdk | >=1.43.0 | 升级 | 已升到 v1.43.0；Go 已升到 1.25.5 |
| `src/core-api` | 已处理 | W202605121455111384290 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384287?from=myTodo&project_id=1) | otelgin | >=0.44.0 | 升级 | 已升到 v0.68.0；与 OpenTelemetry v1.43.0 / Go 1.25.5 兼容 |
| `src/core-api` | 已处理 | W202605121455121384299 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384296?from=myTodo&project_id=1) | golang.org/x/crypto | >=0.45.0 | 升级 | 已升到 v0.50.0；x/net v0.53.0 要求 x/crypto v0.50.0 |
| `src/core-api` | 已处理 | W202605121455121384295 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384292?from=myTodo&project_id=1) | golang.org/x/net | >=0.53.0 | 升级 | 已升到 v0.53.0；Go 已升到 1.25.5 |
| `src/core-api` | 已处理 | W202605121455111384291 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384288?from=myTodo&project_id=1) | github.com/golang-jwt/jwt/v4 | >=4.5.2 | 升级 | 已升到 v4.5.2；兼容 Go 1.25.5 |
| `src/dashboard-front` | 待处理 | W202605121455121384310 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384307?from=myTodo&project_id=1) | minimatch | >=9.0.7 | 升级 lock | 兼容 Node 16 |
| `src/dashboard-front` | 待处理 | W202605121455121384301 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384298?from=myTodo&project_id=1) | http-proxy-middleware | >=2.0.9 | 升级 lock/上游 | 兼容 Node 16 |
| `src/dashboard-front` | 待处理 | W202605121455121384294 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384291?from=myTodo&project_id=1) | html-minifier | 无 | 暂不升 | 无修复建议；由 art-template 引入，需替换链路或申请例外 |
| `src/dashboard-front` | 待处理 | W202605121455121384309 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384306?from=myTodo&project_id=1) | lodash | >=4.18.0 | 升级 | 直接依赖，兼容当前 Vue/Node |
| `src/dashboard-front` | 待处理 | W202605121455121384305 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384302?from=myTodo&project_id=1) | node-forge | >=1.4.0 | 升级 lock | 兼容 Node 16 |
| `src/dashboard-front` | 待处理 | W202605121455111384281 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384278?from=myTodo&project_id=1) | buffer | >=6.14.4 | 不按建议升 | npm registry 无 buffer@6.14.4，且 OSV 未命中 5.7.1 |
| `src/dashboard-front` | 待处理 | W202605121424141384129 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384125?from=myTodo&project_id=1) | path-to-regexp | >=0.1.13 | 升级 express 或 resolutions | 由 express 固定引入 |
| `src/dashboard-front` | 待处理 | W202605121424151384145 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384142?from=myTodo&project_id=1) | webpack-dev-middleware | >=5.3.4 | 升级 lock | 兼容 Node 16 / Webpack 5 |
| `src/dashboard-front` | 待处理 | W202605121424151384134 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384131?from=myTodo&project_id=1) | ws | >=8.17.1 | 升级 lock | 兼容 Node 16 |
| `src/dashboard-front` | 待处理 | W202605121424141384126 | [处理](https://bksec.woa.com/workbench-manage/worksheet-manage/detail/1384123?from=myTodo&project_id=1) | vue-i18n | >=9.14.5 | 升级 | Vue 3 兼容，Node >=16 兼容 |
