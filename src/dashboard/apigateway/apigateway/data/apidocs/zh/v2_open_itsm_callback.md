### 描述

ITSM 工单审批结果回调接口。

ITSM 单据结束后会向回调地址发送 POST 请求，网关据此处理权限申请单据并落库审批结果。

注意：
- 该接口为应用态接口，需经过网关应用认证（`X-Bkapi-Authorization`）
- 回调 token 支持两种方式（优先级从高到低）：
  - 请求体 `callback_token`
  - query 参数 `verify_token`
- 两者都缺失时请求会被拒绝
- 多租户模式下，必须携带请求头 `X-Bk-Tenant-Id`
- 回调来源应用需在白名单配置 `BK_ITSM4_CALLBACK_ALLOWED_APP_CODES` 中（默认：`bk-itsm4`, `cw_aitsm`）

### 输入参数

#### query 参数

| 参数名称 | 参数类型 | 必选 | 描述 |
| -------- | -------- | ---- | ---- |
| verify_token | string | 否 | 回调校验 token；当请求体未提供 `callback_token` 时用于回退校验 |

#### 请求参数

| 参数名称 | 参数类型 | 必选 | 描述 |
| -------- | -------- | ---- | ---- |
| callback_token | string | 否 | 回调校验 token，优先使用该字段 |
| ticket | object | 是 | 工单详情 |

#### ticket

| 参数名称 | 参数类型 | 必选 | 描述 |
| -------- | -------- | ---- | ---- |
| id | string | 是 | ITSM 工单 ID |
| approve_result | bool/string | 否 | 审批结果，支持 `true/false` 或字符串值 |
| form_data | object | 是 | 表单数据，需包含 `apply_record_id`；`grant_dimension` 缺省按 `gateway` 处理 |

#### form_data

| 参数名称 | 参数类型 | 必选 | 描述 |
| -------- | -------- | ---- | ---- |
| apply_record_id | int/string | 是 | 权限申请记录 ID（可传字符串数字） |
| grant_dimension | string | 否 | 授权维度，`gateway` / `resource` / `mcp_server` |

### 请求参数示例

方式一：请求体传 `callback_token`

```json
{
    "callback_token": "cb-token-001",
    "ticket": {
        "id": "itsm-ticket-001",
        "approve_result": true,
        "form_data": {
            "apply_record_id": 10001,
            "grant_dimension": "gateway"
        }
    }
}
```

方式二：query 传 `verify_token`（请求体不传 `callback_token`）

```http
POST /api/v2/open/itsm/callback/?verify_token=verify-token-001
Content-Type: application/json
```

```json
{
    "ticket": {
        "id": "itsm-ticket-002",
        "approve_result": "true",
        "form_data": {
            "apply_record_id": "10002",
            "grant_dimension": "mcp_server"
        }
    }
}
```

### 响应示例

```json
{
    "code": 0,
    "result": true,
    "message": "",
    "data": {
        "result": true,
        "message": "success"
    }
}
```

### 响应参数说明

| 字段 | 类型 | 描述 |
| ---- | ---- | ---- |
| data | object | 结果数据 |

#### data

| 参数名称 | 参数类型 | 描述 |
| -------- | -------- | ---- |
| result | bool | 是否处理成功 |
| message | string | 结果说明 |
