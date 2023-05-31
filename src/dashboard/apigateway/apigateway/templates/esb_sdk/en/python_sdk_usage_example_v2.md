SDK usage examples for the component API {{component_name}} under the system {{system_name}} are as follows:

- get_client_by_request, suitable for front and backend interaction, can get django request scenario

```python
    from {{package_prefix}}.shortcuts import get_client_by_request

    # A django request needs to be provided, and the client can obtain the current username from the request
    # or obtain the user login info from Cookies. In addition, it supports obtaining the default bk_app_code,
    # bk_app_secret, and endpoint from django settings, which can be also be specified by parameters.
    client = get_client_by_request(request)

    # Set whether to access the test environment of the third-party system, the default value is False, to access its official environment
    # client.set_use_test_env(True)

    # Set the timeout for accessing the component API, in seconds
    # client.set_timeout(10)

    result = client.{{system_name|lower}}.{{component_name}}({"key": "value"})
```

- get_client_by_username, suitable for scenarios where the user is specified directly

```python
    from {{package_prefix}}.shortcuts import get_client_by_username

    # Support to obtain the default bk_app_code, bk_app_secret, endpoint from django settings,
    # and also can be specified by parameters.
    client = get_client_by_username("admin")

    # Set whether to access the test environment of the third-party system, the default value is False, to access its official environment
    # client.set_use_test_env(True)

    # Set the timeout for accessing the component API, in seconds
    # client.set_timeout(10)

    result = client.{{system_name|lower }}.{{component_name}}({"key": "value"})
```
