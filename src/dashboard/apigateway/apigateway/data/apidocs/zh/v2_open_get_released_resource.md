### 描述

查询网关指定环境下已发布的资源详情（包含接口 schema）。

### 输入参数

#### 路径参数

| 参数名称       | 参数类型 | 必选 | 描述     |
|----------------|----------|------|----------|
| gateway_name   | string   | 是   | 网关名称 |
| stage_name     | string   | 是   | 环境名称 |
| resource_name  | string   | 是   | 资源名称 |

### 响应示例

```json
{
  "data": {
    "id": 2448,
    "name": "updatePet",
    "kind": "standard",
    "method": "PUT",
    "path": "/api/v3/pet",
    "schema": {
      "parameters": [
        {
          "name": "petId",
          "in": "path",
          "required": true,
          "schema": {
            "type": "integer"
          }
        }
      ],
      "responses": {
        "200": {
          "description": "Successful operation"
        }
      }
    }
  }
}
```

### 响应参数说明

| 字段 | 类型 | 描述     |
|------|------|----------|
| data | object | 资源详情 |

#### data

| 参数名称 | 参数类型 | 描述         |
|----------|----------|--------------|
| id       | int      | 资源 ID      |
| name     | string   | 资源名称     |
| kind     | string   | 资源类型，`standard`：普通 API，`ai`：模型代理 API |
| method   | string   | 资源请求方法 |
| path     | string   | 资源请求地址 |
| schema   | object   | 资源协议数据 |
