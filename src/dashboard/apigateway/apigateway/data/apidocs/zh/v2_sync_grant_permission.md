### 描述

主动授权，给应用添加访问网关资源的权限


### 输入参数

#### 路径参数

| 参数名称         | 参数类型 | 必选 | 描述   |
|--------------| -------- | ---- | ------ |
| gateway_name | string   | 是   | 网关名 |

#### 请求参数

| 参数名称        | 参数类型 | 必选 | 描述                                      |
| --------------- | -------- | ---- | ----------------------------------------- |
| target_app_code | string   | 是   | 待授权应用                                |
| expire_days     | int      | 否   | 过期时间，单位天；0或不提供时表示永久权限 |
| grant_dimension | string   | 是   | 授权维度，可选值：api(按网关授权)         |

### 请求参数示例

```json
{
    "target_app_code": "bk-sops",
    "expire_days": 360,
    "grant_dimension": "api"
}
```


### 响应示例

status 201
No Content
