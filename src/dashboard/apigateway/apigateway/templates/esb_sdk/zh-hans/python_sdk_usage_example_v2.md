
组件系统 {{system_name}} 下的组件 API {{component_name}} SDK 使用示例如下：

### 1. Django 项目

对于 Django 项目，在 `shortcuts` 包中提供了额外的辅助函数：

#### 1.1 get_client_by_request

- 适用场景：前后端交互，可获取 django request 的场景
- 封装机制：
    - 1. 自动从 django settings 获取蓝鲸应用信息（app_code=settings.BK_APP_CODE，app_secret=settings.BK_APP_SECRET）
    - 2. 自动从 django request 获取当前用户名，从 Cookies 获取登录态

```python
    from {{package_prefix}}.shortcuts import get_client_by_request

    # 支持从 django settings 获取默认的 bk_app_code、bk_app_secret、endpoint，也可通过参数指定。
    client = get_client_by_request(request)

    # 设置是否访问第三方系统的测试环境，默认值为 False，访问其正式环境
    # client.set_use_test_env(True)

    # 设置访问组件 API 的超时时间，单位秒
    # client.set_timeout(10)

    result = client.{{system_name|lower}}.{{component_name}}({"key": "value"})
```

#### 1.2 get_client_by_username

- 适用场景：适用于直接指定用户的场景
- 封装机制：
    - 1. 自动从 django settings 获取蓝鲸应用信息（app_code=settings.BK_APP_CODE，app_secret=settings.BK_APP_SECRET）

```python
    from {{package_prefix}}.shortcuts import get_client_by_username

    # 支持从 django settings 获取默认的 bk_app_code、bk_app_secret、endpoint，也可通过参数指定
    client = get_client_by_username("admin")

    # 设置是否访问第三方系统的测试环境，默认值为 False，访问其正式环境
    # client.set_use_test_env(True)

    # 设置访问组件 API 的超时时间，单位秒
    # client.set_timeout(10)

    result = client.{{system_name|lower }}.{{component_name}}({"key": "value"})
```
