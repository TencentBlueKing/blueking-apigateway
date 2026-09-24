### 描述

回收应用访问网关资源的权限。支持按网关维度或按资源维度回收。

- **网关维度 (gateway)**：回收应用在当前网关下按网关维度授予的权限，以及由按网关权限同步生成的资源权限；不影响其它按资源授予的权限，无需传 `resource_names`。
- **资源维度 (resource)**：仅回收指定资源的权限，需要通过 `resource_names` 指定资源名称列表；资源名称会匹配当前资源及各环境已发布版本中的资源（包括已删除、但仍在已发布版本中生效的资源），不存在的资源名称会被忽略。

OAuth2 内置应用 `public`、`personal` 的权限由系统管理，不支持通过此接口回收。


### 输入参数

#### 路径参数

| 参数名称     | 参数类型 | 必选 | 描述   |
| ------------ | -------- | ---- | ------ |
| gateway_name | string   | 是   | 网关名 |

#### 请求参数

| 参数名称         | 参数类型 | 必选 | 描述                                                                                    |
| ---------------- | -------- | ---- | --------------------------------------------------------------------------------------- |
| target_app_codes | array    | 是   | 待回收权限的应用 bk_app_code 列表，最多 100 个；不支持 OAuth2 内置应用 public、personal |
| grant_dimension  | string   | 是   | 授权维度，可选值：gateway(按网关回收)、resource(按资源回收)                             |
| resource_names   | array    | 否   | 资源名称列表，最多 100 个，grant_dimension 为 resource 时必填                           |

### 请求参数示例

#### 按网关维度回收

```json
{
    "target_app_codes": ["bk-sops"],
    "grant_dimension": "gateway"
}
```

#### 按资源维度回收

```json
{
    "target_app_codes": ["bk-sops"],
    "grant_dimension": "resource",
    "resource_names": ["get_user", "create_user"]
}
```


### 响应示例

```json
{
    "data": null
}
```

### 响应参数说明

| 字段 | 类型   | 描述 |
| ---- | ------ | ---- |
| data | object | 空   |
