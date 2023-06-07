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
make develop
```

当在 editions 目录中增加了新的目录时，为了让 mypy 正确运行，需要同时创建 __init__.pyi 文件，也可以使用以下命令完成：

```shell
make edition-modules
```

## 本地开发


```shell
# 进入项目根路径
cd src/dashboard/apigateway

# 安装依赖包
pip install -r requirements.txt
pip install -r requirements_dev.txt

# 新建数据库(在 MySQL 中操作)
CREATE DATABASE IF NOT EXISTS `bk_apigateway` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
CREATE DATABASE IF NOT EXISTS `bk_esb` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;

# 修改配置文件
cp apigateway/conf/.env.tpl apigateway/conf/.env
# 编辑 apigateway/conf/.env 文件，修改数据库连接信息/域名配置等

# migrate
python manage.py migrate
python manage.py migrate --database bkcore

# 启动进程
python manage.py runserver
```

根据 [dashboard-front/README.md](../dashboard-front/README.md) 拉起前端后, 可以配置`nginx`反向代理


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
