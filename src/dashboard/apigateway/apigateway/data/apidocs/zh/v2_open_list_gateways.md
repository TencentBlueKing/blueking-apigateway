### 描述

查询网关列表

获取可用的网关列表，返回的网关需满足以下条件：
- 已启用
- 公开
- 已发布

### 输入参数
#### query 参数

| 参数名称 | 参数类型 | 必选 | 描述 |
|----------|----------|------|------|
| name | string | 否 | 网关名称，用于过滤网关 |
| fuzzy | boolean | 否 | 是否模糊匹配，true：模糊匹配（name 包含），false：精确匹配 |
| keyword | string | 否 | 搜索关键字，模糊匹配 name 或 description |

### 响应示例

```json
{
    "data": [
        {
            "id": 1,
            "name": "bk-apigateway",
            "description": "蓝鲸 API 网关",
            "maintainers": [
                "admin"
            ],
            "doc_maintainers": [
                "admin"
            ]
        }
    ]
}
```

### 响应参数说明

| 字段 | 类型 | 描述 |
| ---- | ---- | ---- |
| data | array | 结果数据，详细信息请见下面说明 |

data[]

| 参数名称 | 参数类型 | 描述 |
| -------- | -------- | ---- |
| id | int | 网关 ID |
| name | string | 网关名称 |
| description | string | 网关描述 |
| maintainers | array | 网关管理员 |
| doc_maintainers | array | 文档管理员 |
