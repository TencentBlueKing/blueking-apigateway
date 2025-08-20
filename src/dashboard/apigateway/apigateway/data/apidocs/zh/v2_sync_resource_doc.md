### 描述

根据 tar/zip 归档文件，导入资源文档

资源文档 tar/zip 归档文件的准备，请参考网关使用指南：网关 API -> 操作指南 -> 导入网关 API 文档。

### 输入参数

#### 路径参数

| 参数名称         | 参数类型 | 必选 | 描述   |
|--------------| -------- | ---- | ------ |
| gateway_name | string   | 是   | 网关名 |

#### 请求参数

| 参数名称 | 参数类型 | 必选 | 描述                                                                |
| -------- | -------- | ---- | ------------------------------------------------------------------- |
| file     | object   | 是   | 资源文档的归档文件对象，请使用 multipart/form-data 类型传递文件内容 |

### 请求参数示例

`multipart/form-data` 类型，使用 python requests 示例：:

```python
import requests

url = ""

files = {
    "file": open("resource_doc.tar.gz", "rb")
}
response = requests.post(url, files=files)
```

### 响应示例

status 201
No Content |