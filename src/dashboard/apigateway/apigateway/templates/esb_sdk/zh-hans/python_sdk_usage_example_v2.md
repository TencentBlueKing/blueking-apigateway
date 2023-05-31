组件系统 {{system_name}} 下的组件 API {{component_name}} SDK 使用示例如下：

- get_client_by_request，适用于前后端交互，可获取 django request 的场景

```python
    from {{package_prefix}}.shortcuts import get_client_by_request

    # 需提供 django request，client 可从 request 中获取当前用户名或从 Cookies 中获取用户登录态；
    # 并且，支持从 django settings 获取默认的 bk_app_code、bk_app_secret、endpoint，也可通过参数指定。
    client = get_client_by_request(request)

    # 设置是否访问第三方系统的测试环境，默认值为False，访问其正式环境
    # client.set_use_test_env(True)

    # 设置访问组件API的超时时间，单位秒
    # client.set_timeout(10)

    result = client.{{system_name|lower}}.{{component_name}}({"key": "value"})
```

- get_client_by_username，适用于直接指定用户的场景

```python
    from {{package_prefix}}.shortcuts import get_client_by_username

    # 支持从 django settings 获取默认的 bk_app_code、bk_app_secret、endpoint，也可通过参数指定
    client = get_client_by_username("admin")

    # 设置是否访问第三方系统的测试环境，默认值为False，访问其正式环境
    # client.set_use_test_env(True)

    # 设置访问组件API的超时时间，单位秒
    # client.set_timeout(10)

    result = client.{{system_name|lower }}.{{component_name}}({"key": "value"})
```
