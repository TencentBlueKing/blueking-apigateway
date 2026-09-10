# 资源请求路径冲突检测 Web API

两接口沿用资源 Web API 的登录和网关权限校验，只返回提示，不保存资源、不阻断现有保存或发布接口。面向用户的行为说明见 [API 资源路径冲突说明](../../../docs/resource-path-conflicts.md)。

## 全量检测

`GET /backend/gateways/{gateway_id}/resources/-/path-conflicts/`

无请求参数。检测当前网关资源编辑区全部资源，不使用列表筛选条件或分页。返回全部冲突对。

## 单资源检测

`POST /backend/gateways/{gateway_id}/resources/-/path-conflicts/check/`

```json
{"method": "DELETE", "path": "/api/v3/set/{bk_biz_id}/{bk_set_id}", "resource_id": 123}
```

- `method`、`path` 必填，遵循资源请求方法和路径参数校验。
- 新增时不传 `resource_id`；编辑时传当前资源 ID，先检查其属于当前网关，再排除自身。
- 路径是待保存的新路径。只报告它与编辑区其他资源的冲突，不报告其他资源彼此间的冲突。
- 非法请求返回 400；指定资源不存在或属于其他网关时返回 404。

## 返回数据

使用标准 `OKJsonResponse` 响应，其中 `data` 为：

```json
{
  "has_conflicts": true,
  "conflicts": [
    {
      "type": "literal_parameter",
      "resources": [
        {"id": 12, "name": "batch_delete", "method": "DELETE", "path": "/api/v3/set/{bk_biz_id}/batch", "normalized_path": "/api/v3/set/{}/batch"},
        {"id": 123, "name": "delete_set", "method": "DELETE", "path": "/api/v3/set/{bk_biz_id}/{bk_set_id}", "normalized_path": "/api/v3/set/{}/{}"}
      ]
    }
  ]
}
```

- `normalized_path`：参数名替换为 `{}`，按网关路由转换规则忽略尾斜杠。其用途是检测，不会修改资源路径。
- `type=normalized_path`：归一化路径完全相同。
- `type=literal_parameter`：归一化父路径完全相同，末段为固定文本与完整参数。
- 每一项为一个冲突对。同一资源可能出现在多个冲突对中。
- 待新增资源用 `id: null`、`name: ""` 表示；编辑资源使用其现有 ID 和名称。
- 无冲突时返回 `{"has_conflicts": false, "conflicts": []}`。

请求方法相同或任一方为 `ANY` 才报告重叠。完整静态路径与末段参数的重叠也提示为 `literal_parameter`，但这不代表参数一定优先匹配。接口不推断实际命中资源，不展开环境变量，不检测匹配子路径产生的通配符重叠，也不检测上述两类以外的路径交叉。

这是 Dashboard 内部 Web API，采用视图 Swagger serializer 描述；没有新增 OpenAPI 网关公开资源，因此不添加 `data/apigw-definitions` 或公开 `data/apidocs` 条目。
