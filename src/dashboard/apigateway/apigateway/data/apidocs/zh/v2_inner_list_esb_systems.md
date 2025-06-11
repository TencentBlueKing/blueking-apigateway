### 描述

查询组件系统列表


### 输入参数

#### 路径参数

| 参数名称           | 参数类型    | 必选 | 描述    |
|----------------|---------|----|-------|
| user_auth_type | string  | 是  | 用户身份类型 |


### 请求参数示例

```json
{}
```


### 响应示例
```
{
  "data": [
    {
      "id": 1,
      "name": "BK_DOCS_CENTER",
      "description": "文档中心",
      "description_en": "Docs Center",
      "maintainers": [
        "admin"
      ],
      "tag": ""
    }
  ]
}
```

### 响应参数说明

| 字段    | 类型   | 描述                               |
| ------- | ------ | ---------------------------------- |
| data    | array  | 结果数据，详细信息请见下面说明     |

#### data

| 参数名称        | 参数类型   | 描述   |
|-------------|--------|------|
| id          | int    | 组件ID |
| name        | string | 组件名称 |
| description | string | 系统描述 |
| maintainers | array  | 管理员  |
| tag         | string | 标签   |
