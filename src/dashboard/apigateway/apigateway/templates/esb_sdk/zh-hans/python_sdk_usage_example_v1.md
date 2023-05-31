组件系统 {{system_name}} 下的组件 API {{component_name}} SDK 使用示例如下：

- get_client_by_request，适用于前后端交互，可获取 django request 的场景

```python
    from {{package_prefix}}.shortcuts import get_client_by_request

    # 从 django settings 获取蓝鲸应用信息（app_code=settings.APP_CODE，app_secret=settings.SECRET_KEY）
    # 参数 request 为 django Request 对象，其中包含用户信息
    client = get_client_by_request(request)

    # 设置是否访问第三方系统的测试环境，默认值为False，访问其正式环境
    # client.set_use_test_env(True)

    # 设置访问组件API的超时时间，单位秒
    # client.set_timeout(10)

    # 组件API请求参数
    kwargs = {
    }

    result = client.{{system_name|lower}}.{{component_name}}(kwargs)
```

- get_client_by_user，适用于直接指定用户的场景

```python
    from {{package_prefix}}.shortcuts import get_client_by_user

    # 从 django settings 获取蓝鲸应用信息（app_code=settings.APP_CODE，app_secret=settings.SECRET_KEY）
    # 参数 user 为 django user 对象或用户名，指定当前用户
    client = get_client_by_user(user="xxx")

    # 设置是否访问第三方系统的测试环境，默认值为False，访问其正式环境
    # client.set_use_test_env(True)

    # 设置访问组件API的超时时间，单位秒
    # client.set_timeout(10)

    # 组件API请求参数
    kwargs = {
    }

    result = client.{{system_name|lower }}.{{component_name}}(kwargs)
```

- ComponentClient，适用于指定蓝鲸应用及用户的场景

```python
    from {{package_prefix}}.client import ComponentClient

    # 蓝鲸应用信息
    app_code = "xxx"
    app_secret = "xxx"

    # 蓝鲸应用信息app_code, app_secret如未提供，从环境配置获取
    client = ComponentClient(
        # 如未提供蓝鲸应用信息app_code, app_secret，将从 django settings 中获取
        app_code=app_code,
        app_secret=app_secret,
        # 通用参数，可添加用户信息
        common_args={"access_token": "xxx"},
        # 设置访问组件API的超时时间，单位秒
        timeout=10,
    )

    # 设置是否访问第三方系统的测试环境，默认值为False，访问其正式环境
    # client.set_use_test_env(True)

    # 设置访问组件API的超时时间，单位秒
    # client.set_timeout(10)

    # 组件API请求参数
    kwargs = {
    }

    result = client.{{system_name|lower}}.{{component_name}}(kwargs)
```
