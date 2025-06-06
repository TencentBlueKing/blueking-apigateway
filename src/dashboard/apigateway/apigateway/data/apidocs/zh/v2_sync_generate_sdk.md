### 描述

创建资源版本对应的 SDK

### 输入参数

#### 路径参数

| 参数名称         | 参数类型 | 必选 | 描述   |
|--------------| -------- | ---- | ------ |
| gateway_name | string   | 是   | 网关名 |

#### 请求参数

| 参数名称         | 参数类型      | 必选 | 描述                                                     |
| ---------------- | ------------- | ---- | -------------------------------------------------------- |
| resource_version | string        | 是   | 资源版本的版本号                                         |
| languages        | array[string] | 否   | 需要生成SDK的语言列表，可选值：python，默认为 python SDK |
| version          | string        | 否   | SDK 版本号，未设置时，将使用资源版本的版本号             |

### 请求参数示例

```json
{
    "resource_version": "1.0.1",
    "languages": ["python"],
    "version": "1.0.1"
}
```



### 响应示例

```json
{
    "data": [
        {
            "name": "bkapi-test",
            "version": "1.0.1",
            "url": "http://demo.example.com/bkapi-test-1.0.1.tar.gz"
        }
    ]
}
```

### 响应参数说明

| 字段    | 类型   | 描述                               |
| ------- | ------ | ---------------------------------- |
| data    | array  | 结果数据，详细信息请见下面说明     |

#### data

| 名称    | 类型   | 说明         |
| ------- | ------ | ------------ |
| name    | string | SDK 名称     |
| version | string | SDK 版本号   |
| url     | string | SDK 下载地址 |