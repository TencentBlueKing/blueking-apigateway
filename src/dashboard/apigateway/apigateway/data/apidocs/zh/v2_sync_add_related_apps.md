### 描述

添加网关的关联应用 (related_app)

### 输入参数

| 参数名称 | 参数类型 | 参数位置 | 描述 |
| -------- | -------- | -------- | ---- |
| gateway_name | string | path | 网关名称 |
| related_app_codes | array | body | 应用编码列表 |

### 请求参数示例

```json
{
    "related_app_codes": ["bk_apigateway"]
}
```

### 响应示例

status 201
No Content

