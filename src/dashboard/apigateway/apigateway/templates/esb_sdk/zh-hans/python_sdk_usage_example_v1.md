
组件系统 {{system_name}} 下的组件 API {{component_name}} SDK 使用示例如下：

### 1. Django 项目

对于 Django 项目，在 `shortcuts` 包中提供了额外的辅助函数：

#### 1.1 get_client_by_request

- 适用场景：前后端交互，可获取 django request 的场景
- 封装机制：
    - 1. 自动从 django settings 获取蓝鲸应用信息（app_code=settings.BK_APP_CODE，app_secret=settings.BK_APP_SECRET）
    - 2. 自动从 django request 获取当前用户名，从 Cookies 获取登录态
    - 3. 如果安装了 `bkoauth`会自动通过 bkoauth sdk 生成 access_token, 将 access_token 放入认证头 (注意意`bkapi-component-open` 包不依赖bkauth sdk (默认没有装))

```python
    from {{package_prefix}}.shortcuts import get_client_by_request

    client = get_client_by_request(request)

    # 设置是否访问第三方系统的测试环境，默认值为 False，访问其正式环境
    # client.set_use_test_env(True)

    # 设置访问组件 API 的超时时间，单位秒
    # client.set_timeout(10)

    # 组件 API 请求参数
    kwargs = {
    }

    result = client.{{system_name|lower}}.{{component_name}}(kwargs)
```

#### 1.2 get_client_by_user

- 适用场景：适用于直接指定用户的场景
- 封装机制：
    - 1. 自动从 django settings 获取蓝鲸应用信息（app_code=settings.BK_APP_CODE，app_secret=settings.BK_APP_SECRET）
    - 2. 如果安装了 `bkoauth`会自动通过 bkoauth sdk 生成 access_token, 将 access_token 放入认证头 (注意意`bkapi-component-open` 包不依赖bkauth sdk (默认没有装))

```python
    from {{package_prefix}}.shortcuts import get_client_by_user

    # 参数 user 为 django user 对象或用户名，指定当前用户
    client = get_client_by_user(user="xxx")

    # 设置是否访问第三方系统的测试环境，默认值为 False，访问其正式环境
    # client.set_use_test_env(True)

    # 设置访问组件 API 的超时时间，单位秒
    # client.set_timeout(10)

    # 组件 API 请求参数
    kwargs = {
    }

    result = client.{{system_name|lower }}.{{component_name}}(kwargs)
```

### 2. 非 Django 项目

- 适用场景：非 Django 的 Python 项目，指定蓝鲸应用及用户的场景

```python
    from {{package_prefix}}.client import ComponentClient

    # 蓝鲸应用信息
    app_code = "xxx"
    app_secret = "xxx"

    # 蓝鲸应用信息 app_code, app_secret 如未提供，从环境配置获取
    client = ComponentClient(
        # 如未提供蓝鲸应用信息 app_code, app_secret，将从 django settings 中获取
        app_code=app_code,
        app_secret=app_secret,
        # 通用参数，可添加用户信息
        common_args={"access_token": "xxx"},
        # 设置访问组件 API 的超时时间，单位秒
        timeout=10,
    )

    # 设置是否访问第三方系统的测试环境，默认值为 False，访问其正式环境
    # client.set_use_test_env(True)

    # 设置访问组件 API 的超时时间，单位秒
    # client.set_timeout(10)

    # 组件 API 请求参数
    kwargs = {
    }

    result = client.{{system_name|lower}}.{{component_name}}(kwargs)
```
