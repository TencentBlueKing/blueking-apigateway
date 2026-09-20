# dashboard

## 初始化开发环境

```shell
make init
```

## 多版本管理

```shell
# 查看当前版本
make edition

# 切换开源版
make edition-ee

# 进入开发模式
make edition-develop
```

当在 editions 目录中增加了新的目录时，为了让 mypy 正确运行，需要同时创建 __init__.pyi 文件，也可以使用以下命令完成：

```shell
make edition-modules
```

## 本地开发

准备数据库

```sql
# 新建数据库(在 MySQL 中操作)
CREATE DATABASE IF NOT EXISTS `bk_apigateway` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
CREATE DATABASE IF NOT EXISTS `bk_esb` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
```

```shell
# 进入项目根路径
cd src/dashboard

# 建议使用虚拟环境
# 安装依赖包
uv sync


# 修改配置文件
cd apigateway
cp apigateway/conf/.env.tpl apigateway/conf/.env
# 编辑 apigateway/conf/.env 文件，修改数据库连接信息/域名配置等

# migrate
python manage.py migrate
python manage.py migrate --database bkcore

# 启动进程
python manage.py runserver
```

根据 [dashboard-front/README.md](../dashboard-front/README.md) 拉起前端后, 可以配置`nginx`反向代理

一份示例的 Nginx 配置（只包含 server 部分）如下：

```nginx
    server {
        listen        80;
        server_name   dev-apigw.example.com;

        location / {
            proxy_pass http://127.0.0.1:8888;
        }
        location /backend/ {
            proxy_pass http://127.0.0.1:8000;
        }
    }
```

## 如何维护插件类型

1. 在本地环境中，执行 `make load_fixtures` 命令，保证数据库数据和线上一致；
2. 启动本地开发服务 `python manage.py runserver`，进入 /backend/admin42/plugin/ 修改相关模型；
   - 对于插件类型，code 确定后不可随便修改，会影响其他环境的数据迁移；
   - 对于插件表单，注意提供中文（`language=""`）和英文（`language="en"`）两个版本的记录；
3. 确认数据库数据正确之后，执行 `make dump_fixtures` 命令自动更新 apigateway/fixtures/plugins.yaml 文件，确认写入内容是否符合预期。

## 注意概念转换: API -> Gateway

最早网关的概念叫 `API`, 后来重构转换为 `Gateway`

希望整体代码统一逻辑, 所有地方出现网关都是 `Gateway`

后续新增代码, 必须使用统一的`Gateway`概念

例外:(当前)
1. 前端还在使用`api_id`等概念(出参/入参) => 需要统一修改
2. db以及orm的foreign key还是`api=`以及`api_id=`, 涉及managers.py以及所有 `X.objects.filter(api=gateway)`


## 恢复历史发布入口

发布状态依赖 `core_publish_event`。清理任务保留每个环境、数据面（包括旧数据的空数据面）
最新发布历史的全部事件，其他过期事件仍按 `CLEAN_TABLE_INTERVAL_DAYS` 清理。
无事件的发布历史在创建后的 10 分钟内显示待发布，超过该时间显示失败并允许重新发布。
此处失败表示发布结果无法确认，不代表数据面实际部署失败。

如果需要为某个网关补充人工恢复记录，可在 Dashboard 运行环境的 `manage.py` 所在目录执行：

```bash
# 默认只预览整个网关，也可以使用 --stage prod 限定环境
python manage.py recover_stage_publish --gateway-id 100194

# 核对预览后写入恢复事件
python manage.py recover_stage_publish --gateway-id 100194 --stage prod \
  --apply --operator kunliangwu --reason "历史发布事件缺失，恢复重新发布入口"
```

命令仅处理各环境、数据面最新的、无事件且超过 10 分钟的发布历史；有事件、未超时或创建时间
缺失的记录会跳过。默认不写入；`--apply` 必须同时提供操作人（不超过 32 字符）和原因。
写入时使用现有发布锁并重新检查最新发布和事件，重复执行不会重复补记录。
逐项输出环境、数据面、发布 ID 和处理结果；若中途失败，已输出恢复成功的记录已提交，可重试。

恢复记录将该次发布标记为失败，记录原部署结果未知、操作人和原因；不修改环境启停状态、
资源版本或线上路由，也不会自动发起发布。刷新页面后仍需通过其他配置校验并手动重新发布。
该命令不支持可编程网关的部署恢复，也不强制终止已有事件的发布。它不会取消后台任务，
延迟任务仍可能继续上报事件；人工恢复前应确认旧发布已不再执行。
