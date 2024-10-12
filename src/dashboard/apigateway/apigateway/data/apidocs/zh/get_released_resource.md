### 描述

查询网关指定环境下，已发布的资源详情，包含接口协议信息(来源资源openapi、swagger协议定义)


### 输入参数

#### 路径参数

| 参数名称          | 参数类型 | 必选 | 描述    |
|---------------| -------- | ---- |-------|
| api_name      | string   | 是   | 网关名   |
| stage_name    | string   | 是   | 环境名   |
| resource_name | string   | 是   | 资源名称  |
### 请求参数示例

```json
{}
```

### SDK 调用示例

```python
from bkapi.bk_apigateway.shortcuts import get_client_by_request

client = get_client_by_request(request)
result = client.api.get_released_resources(
    {},
    path_params={
        "api_name": "demo",
        "stage_name": "prod",
        "resource_name":"updatePet"
    },
)
```


### 响应示例

```json
{
  "data": {
    "id": 2448,
    "name": "updatePet",
    "method": "PUT",
    "path": "/api/v3/pet",
    "schema": {
      "requestBody": {
        "description": "Update an existent pet in the store",
        "content": {
          "application/json": {
            "schema": {
              "required": [
                "name",
                "photoUrls"
              ],
              "type": "object",
              "properties": {
                "id": {
                  "type": "integer",
                  "format": "int64",
                  "example": 10
                },
                "name": {
                  "type": "string",
                  "example": "doggie"
                },
                "category": {
                  "type": "object",
                  "properties": {
                    "id": {
                      "type": "integer",
                      "format": "int64",
                      "example": 1
                    },
                    "name": {
                      "type": "string",
                      "example": "Dogs"
                    }
                  },
                  "xml": {
                    "name": "category"
                  }
                },
                "photoUrls": {
                  "type": "array",
                  "xml": {
                    "wrapped": true
                  },
                  "items": {
                    "type": "string",
                    "xml": {
                      "name": "photoUrl"
                    }
                  }
                },
                "tags": {
                  "type": "array",
                  "xml": {
                    "wrapped": true
                  },
                  "items": {
                    "type": "object",
                    "properties": {
                      "id": {
                        "type": "integer",
                        "format": "int64"
                      },
                      "name": {
                        "type": "string"
                      }
                    },
                    "xml": {
                      "name": "tag"
                    }
                  }
                },
                "status": {
                  "type": "string",
                  "description": "pet status in the store",
                  "enum": [
                    "available",
                    "pending",
                    "sold"
                  ]
                }
              },
              "xml": {
                "name": "pet"
              }
            }
          }
        },
        "required": true
      },
      "responses": {
        "200": {
          "description": "Successful operation",
          "content": {
            "application/json": {
              "schema": {
                "required": [
                  "name",
                  "photoUrls"
                ],
                "type": "object",
                "properties": {
                  "id": {
                    "type": "integer",
                    "format": "int64",
                    "example": 10
                  },
                  "name": {
                    "type": "string",
                    "example": "doggie"
                  },
                  "category": {
                    "type": "object",
                    "properties": {
                      "id": {
                        "type": "integer",
                        "format": "int64",
                        "example": 1
                      },
                      "name": {
                        "type": "string",
                        "example": "Dogs"
                      }
                    },
                    "xml": {
                      "name": "category"
                    }
                  },
                  "photoUrls": {
                    "type": "array",
                    "xml": {
                      "wrapped": true
                    },
                    "items": {
                      "type": "string",
                      "xml": {
                        "name": "photoUrl"
                      }
                    }
                  },
                  "tags": {
                    "type": "array",
                    "xml": {
                      "wrapped": true
                    },
                    "items": {
                      "type": "object",
                      "properties": {
                        "id": {
                          "type": "integer",
                          "format": "int64"
                        },
                        "name": {
                          "type": "string"
                        }
                      },
                      "xml": {
                        "name": "tag"
                      }
                    }
                  },
                  "status": {
                    "type": "string",
                    "description": "pet status in the store",
                    "enum": [
                      "available",
                      "pending",
                      "sold"
                    ]
                  }
                },
                "xml": {
                  "name": "pet"
                }
              }
            }
          }
        },
        "400": {
          "description": "Invalid ID supplied"
        },
        "404": {
          "description": "Pet not found"
        },
        "422": {
          "description": "Validation exception"
        }
      }
    }
  },
  "code": 0,
  "result": true,
  "message": "OK"
}
```

### 响应参数说明

| 字段    | 类型   | 描述                               |
| ------- | ------ | ---------------------------------- |
| code    | int    | 返回码，0 表示成功，其它值表示失败 |
| message | string | 错误信息                           |
| data    | object | 结果数据，详细信息请见下面说明     |

#### data

| 参数名称   | 参数类型 | 描述             |
|--------| -------- |----------------|
| id     | int      | ID             |
| name   | string   | 资源名称           |
| method | string   | 资源请求方法         |
| path   | string   | 资源请求地址         |
| schema | object   | 资源协议数据，详情见下面说明 |

#### data.schema
| 参数名称   | 参数类型 | 描述               |
|--------| -------- |------------------|
| requestBody     | object      | 资源请求body协议       |
| parameters     | object      | 资源请求parameters协议 |
| responses   | string   | 资源response协议     |

> schema格式与 openapi3.0 的保持一致：具体见：[OpenAPI Specification](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.1.md)