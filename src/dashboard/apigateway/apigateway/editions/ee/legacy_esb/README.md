# README.md

> 注意：PaaS2/ESB 迁移数据至新版 BK-ESB，全部在包 legacy_esb 中处理，禁止其他模块依赖此包，待数据迁移完毕，可直接去除此包

## 迁移 PaaS2/ESB 核心数据至新版 BK-ESB

进入服务 `bk-apigateway-dashboard-web` 的容器，然后执行以下指令：

```
检查数据
- python manager.py pre_check_core_data

检查数据成功，则执行以下指令同步数据
- python manage.py fix_legacy_data
- python manage.py clear_ng_core_data
- python manage.py sync_core_data
- python manage.py assert_core_data
```


## 迁移 PaaS2/ESB 自助接入组件至 API Gateway

进入服务 `bk-apigateway-dashboard-web` 的容器，然后执行以下指令：
```
检查数据
- python manage.py pre_check_buffet_data

检查数据成功，则执行以下指令同步数据
- python manage.py sync_buffet_definitions
```

迁移后，还需要更新旧版接入层 nginx 的配置，添加以下 location
```
location ~ ^/api/c/self-service-api/(.*) {
    rewrite /api/c/self-service-api/(.*)$ /api/bk-esb-buffet/prod/$1 break;
    proxy_pass http://BKAPI_HOST;

    proxy_pass_header Server;
    proxy_set_header X-Request-Uri $request_uri;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Scheme $scheme;
    proxy_set_header Host $http_host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $http_host;
    proxy_redirect off;
    proxy_read_timeout 600;
}
```

## 迁移数据的指令列表

python manage.py assert_core_data
- 迁移完成后，校验迁移前后数据是否一致

python manage.py clear_ng_core_data
- 删除新版 BK-ESB 中的数据，主要包括：ComponentSystem、DocCategory、SystemDocCategory、ESBChannel、ComponentDoc、AppComponentPermission
- 迁移数据时，会保持新旧版数据ID一致，因此如果新版中已生成数据，需将生成的数据删除，再进行迁移，以防止数据冲突

python manage.py fix_legacy_data
- 修复旧版数据，如旧版文档分类名称，可能重复，迁移前，需去除重复的数据

python manage.py pre_check_core_data
- 迁移前，预检数据，校验数据是否满足迁移条件，如文档分类名称成否有重复

python manage.py sync_core_data
- 迁移 PaaS2/ESB 至新版 BK-ESB

python manage.py sync_buffet_definitions
- 迁移 PaaS2/ESB 自助接入组件至 API Gateway
- 最大超时时间调整为 600 秒
- 如果自助接入组件配置 extra_headers 中，包含不符合要求(^[a-zA-Z0-9-_]{1,100}$)的请求头，需要调整请求头后才能迁移，如果请求头包含下划线（_），迁移时，将被转为中折线（-）

python manage.py export_buffet_to_resources
- 将 PaaS2/ESB 中自定义组件配置，导出为网关 Swagger 资源配置文件
