### 描述

ITSM 工单审批结果回调接口。

ITSM 单据结束后会向回调地址发送 POST 请求，网关据此处理权限申请单据并落库审批结果。

注意：
- 该接口为应用态接口，需经过网关应用认证（`X-Bkapi-Authorization`）
- 回调 token 仅支持请求体字段 `callback_token`
- `callback_token` 缺失时请求会被拒绝
- 多租户模式下，必须携带请求头 `X-Bk-Tenant-Id`
- 回调来源应用需在白名单配置 `BK_ITSM4_CALLBACK_ALLOWED_APP_CODES` 中（默认跟随 `BK_ITSM4_CALLBACK_APP_CODE`：非多租户环境 `bk-itsm4`，多租户环境 `cw_aitsm`）

### 输入参数

#### query 参数

| 参数名称 | 参数类型 | 必选 | 描述 |
| -------- | -------- | ---- | ---- |

#### 请求参数

| 参数名称 | 参数类型 | 必选 | 描述 |
| -------- | -------- | ---- | ---- |
| callback_token | string | 是 | 回调校验 token |
| ticket | object | 是 | 工单详情 |

#### ticket

| 参数名称 | 参数类型 | 必选 | 描述 |
| -------- | -------- | ---- | ---- |
| id | string | 是 | ITSM 工单 ID |
| approve_result | bool | 是 | 审批结果 |
| form_data | object | 是 | 表单数据，需包含 `apply_record_id` 和 `grant_dimension` |

#### form_data

| 参数名称 | 参数类型 | 必选 | 描述 |
| -------- | -------- | ---- | ---- |
| apply_record_id | int/string | 是 | 权限申请记录 ID（可传字符串数字） |
| grant_dimension | string | 是 | 授权维度，`gateway` / `resource` / `mcp_server` |

### 请求参数示例

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
