### 描述

查询网关公钥

### 输入参数

| 参数名称 | 参数类型 | 参数位置 | 描述 |
| -------- | -------- | -------- | ---- |
| gateway_name | string | path| 网关名称 |

### 请求参数示例

### 响应示例

```json
{
    "data": {
        "issuer": "APIGW",
        "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnZXkNSGhJO7lb7JDXhZ9\niJ7/DN/zqA4IULQZupegG2VJRc4pRogVjfYsWS9PmEt5/z1MbYtlo+GGxmV9gsOR\njV2g3zXaylDcFsu9mI+ptDX7LXV399wG5dXnt58LpUrwxUq9kQzhKGlbbtvUFcLb\np+3Gj/e1940T1O8PX6GPJGz1b7Ai3imWIpd/gExTh4Yml6Bh0cpslvQjbs7sYRSs\nXNyqZslWjO9/cdtYIHVOFmDPBQqT7Sr1++0sH8kqd0PJCbBS1MpWxDMQQfCk7uO5\nfP0gp0qquhFxmwg7Sh+673nLOwrWBkDtrddjSMWiWHvIQyHLEw8zCg/N3HK2JE2p\nRQIDAQAB\n-----END PUBLIC KEY-----"
    },
    "result": true,
    "message": "",
    "code": 0
}
```

### 响应参数说明

| 字段    | 类型   | 描述                               |
| ------- | ------ | ---------------------------------- |
| data    | object | 结果数据，详细信息请见下面说明     |

data

| 参数名称    | 参数类型 | 描述       |
| ----------- | -------- | ---------- |
| issuer      | string   | 颁发者     |
| public_key  | string   | 公钥       |
