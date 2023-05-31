SDK usage examples for the component API {{component_name}} under the system {{system_name}} are as follows:

- get_client_by_request, suitable for front and backend interaction, can get django request scenario

```python
    from {{package_prefix}}.shortcuts import get_client_by_request

    # Get app info from django settings (app_code=settings.BK_APP_CODE, app_secret=settings.BK_APP_SECRET)
    # The parameter request is a django Request object that contains user information
    client = get_client_by_request(request)

    # Set whether to access the test environment of the third-party system, the default value is False, to access its official environment
    # client.set_use_test_env(True)

    # Set the timeout for accessing the component API, in seconds
    # client.set_timeout(10)

    # Component API request parameters
    kwargs = {
    }

    result = client.{{system_name|lower}}.{{component_name}}(kwargs)
```

- get_client_by_user, suitable for scenarios where the user is specified directly

```python
    from {{package_prefix}}.shortcuts import get_client_by_user

    # Get app info from django settings (app_code=settings.BK_APP_CODE, app_secret=settings.BK_APP_SECRET)
    # The user argument is a django user object or username, specifying the current user
    client = get_client_by_user(user="xxx")

    # Set whether to access the test environment of the third-party system, the default value is False, to access its official environment
    # client.set_use_test_env(True)

    # Set the timeout for accessing the component API, in seconds
    # client.set_timeout(10)

    # Component API request parameters
    kwargs = {
    }

    result = client.{{system_name|lower }}.{{component_name}}(kwargs)
```

- ComponentClient, suitable for scenarios where the app and user are specified directly

```python
    from {{package_prefix}}.client import ComponentClient

    # app info
    app_code = "xxx"
    app_secret = "xxx"

    # application information app_code, app_secret if not provided, obtained from the environment configuration
    client = ComponentClient(
        # If app_code, app_secret is not provided, it will be retrieved from django settings
        app_code=app_code,
        app_secret=app_secret,
        # General parameters, can add user information
        common_args={"access_token": "xxx"},
        # Set the timeout for accessing the component API, in seconds
        timeout=10,
    )

    # Set whether to access the test environment of the third-party system, the default value is False, to access its official environment
    # client.set_use_test_env(True)

    # Set the timeout for accessing the component API, in seconds
    # client.set_timeout(10)

    # Component API request parameters
    kwargs = {
    }

    result = client.{{system_name|lower}}.{{component_name}}(kwargs)
```
