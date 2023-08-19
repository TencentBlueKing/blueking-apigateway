# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
#     http://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.
#
# We undertake not to change the open source license (MIT license) applicable
# to the current version of the project delivered to anyone in the future.
#


ZH_RESOURCE_DOC_TMPL = """\
### 描述

这是一个描述

### 输入参数
| 参数名称     | 参数类型     | 必选   | 描述             |
| ------------ | ------------ | ------ | ---------------- |
| demo         | string       | 否     | 这是一个样例     |


### 调用示例
```python
from bkapi.__GATEWAY_NAME__.shortcuts import get_client_by_request

client = get_client_by_request(request)
result = client.api.api_test({}, path_params={}, headers=None, verify=True)
```

### 响应示例
```python

```

### 响应参数说明
| 参数名称     | 参数类型   | 描述                           |
| ------------ | ---------- | ------------------------------ |
|              |            |                                |
"""


EN_RESOURCE_DOC_TMPL = """\
### Description

This is a description

### Parameters

| Name         | Type         | Required   | Description      |
| ------------ | ------------ | ---------- | ---------------- |
| demo         | string       | Yes        | This is a demo   |

### Request Example
```python
from bkapi.__GATEWAY_NAME__.shortcuts import get_client_by_request

client = get_client_by_request(request)
result = client.api.api_test({}, path_params={}, headers=None, verify=True)
```

### Response Example
```python

```

### Response Parameters
| Name         | Type       | Description                    |
| ------------ | ---------- | ------------------------------ |
|              |            |                                |
"""
