### 描述

创建申请资源权限的申请单据


### 输入参数

#### 路径参数

| 参数名称            | 参数类型 | 必选 | 描述                  |
|-----------------| -------- | ---- |---------------------|
| gateway_name    | string   | 是   | 网关名称                |

#### 请求参数

| 参数名称                   | 参数类型       | 必选 | 描述                          |
|------------------------|------------|----|-----------------------------|
| target_app_code        | string     | 是  | 申请权限的应用，应于当前请求的应用一致         |
| resource_ids           | array[int] | 否  | 资源ID列表                      |
| reason                 | string     | 否  | 申请理由                        |
| expire_days            | int        | 是  | 过期时间，0：永久，180：6个月，360：12个月  |
| grant_dimension        | string     | 是  | 授权维度，api：按网关，resource：按资源   |

### 请求参数示例

```json
{
  "target_app_code": "",
  "resource_ids": [],
  "reason": "",
  "expire_days": 180,
  "grant_dimension": "api"
}
```


### 响应示例

```json
{
  "data": {
    "record_id": 6
  }
}

```

### 响应参数说明

| 字段    | 类型     | 描述                               |
| ------- |--------| ---------------------------------- |
| data    | object | 结果数据，详细信息请见下面说明     |

#### data

| 参数名称          | 参数类型   | 描述         |
|---------------|--------|------------|
| record_id     | int    | 权限申请单的单据ID |

