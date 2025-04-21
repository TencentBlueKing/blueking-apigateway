### 描述

资源权限申请记录列表


### 输入参数

#### 路径参数

| 参数名称               | 参数类型   | 必选 | 描述                                                                 |
|--------------------|--------|----|--------------------------------------------------------------------|
| target_app_code    | string | 是  | 申请权限的应用，应于当前请求的应用一致                                                |
| applied_by         | string | 否  | 申请人                                                                |
| applied_time_start | int    | 否  | 申请开始时间                                                             |
| applied_time_end   | int    | 否  | 申请截止时间                                                             |
| apply_status       | string | 否  | 申请状态，partial_approved：部分通过，approved：全部通过，rejected：全部驳回，pending：待审批 |
| query              | string | 否  | 查询条件                                                               |


### 请求参数示例

```json
{}
```


### 响应示例

```json
{
  "data": [
    {
      "id": 1,
      "bk_app_code": "test",
      "applied_by": "admin",
      "applied_time": "2025-01-01 00:00:00 +0800",
      "handled_by": [
        "admin"
      ],
      "handled_time": null,
      "apply_status": "pending",
      "apply_status_display": "待审批",
      "grant_dimension": "api",
      "comment": "",
      "reason": "",
      "expire_days": 180,
      "gateway_name": "test"
    }
  ]
}
```

### 响应参数说明

| 字段    | 类型   | 描述                               |
| ------- | ------ | ---------------------------------- |
| data    | array  | 结果数据，详细信息请见下面说明     |

#### data

| 参数名称                 | 参数类型   | 描述                        |
|----------------------|--------|---------------------------|
| id                   | int    | 申请ID                      |
| bk_app_code          | string | 蓝鲸应用编码                    |
| applied_by           | string | 申请人                       |
| applied_time         | string | 申请时间                      |
| handled_by           | array  | 审批人                       |
| handled_time         | int    | 审批时间                      |
| apply_status         | string | 审批状态                      |
| apply_status_display | string | 审批状态描述                    |
| grant_dimension      | string | 授权维度，api：按网关，resource：按资源 |
| comment              | string | 审批内容                      |
| reason               | string | 申请理由                      |
| expire_days          | int    | 过期时间                      |
| gateway_name         | string | 网关名称                      |
