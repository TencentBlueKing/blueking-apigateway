### 描述

主动授权，给应用添加访问网关资源的权限。支持按网关维度或按资源维度授权。

- **网关维度 (gateway)**：授权整个网关的所有资源（包括后续新建资源），无需传 `resource_names`。
- **资源维度 (resource)**：仅授权指定资源，需要通过 `resource_names` 指定资源名称列表。


### 输入参数

#### 路径参数

| 参数名称         | 参数类型 | 必选 | 描述   |
|--------------| -------- | ---- | ------ |
| gateway_name | string   | 是   | 网关名 |

#### 请求参数

| 参数名称        | 参数类型 | 必选 | 描述                                                                                     |
| --------------- | -------- | ---- |----------------------------------------------------------------------------------------|
| target_app_code | string   | 是   | 待授权应用的 bk_app_code                                                                     |
| expire_days     | int      | 否   | 过期时间，单位天；0或不提供时表示永久权限                                                                  |
| grant_dimension | string   | 是   | 授权维度，可选值：gateway(按网关授权)、resource(按资源授权)         |
| resource_names  | array    | 否   | 资源名称列表，grant_dimension 为 resource 时必填                                                   |

### 请求参数示例

#### 按网关维度授权

```json
{
    "target_app_code": "bk-sops",
    "expire_days": 360,
    "grant_dimension": "gateway"
}
```

#### 按资源维度授权

```json
{
    "target_app_code": "bk-sops",
    "expire_days": 180,
    "grant_dimension": "resource",
    "resource_names": ["get_user", "create_user"]
}
```


### 响应示例

status 201
No Content
