## 安装

### maven
```
<dependency>
    <groupId>com.tencent.bkapi</groupId>
    <artifactId>{gateway_name}</artifactId>
    <version>{sdk_version}</version>
</dependency>
```

### grade

```
implementation 'com.tencent.bkapi:{gateway_name}:{sdk_version}'

```

## 使用 SDK

假定网关 {{gateway_name}} 下存在网关 API {{resource_name}}。


{% include "api_sdk/zh-hans/python_sdk_usage_example.md" %}
