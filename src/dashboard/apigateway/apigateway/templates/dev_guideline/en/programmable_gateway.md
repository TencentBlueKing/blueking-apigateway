## Development Guide

{% if language == "python" %}

### Pull the code to local

```bash
git clone {{repo_url}}
```

### Set environment variables

```bash
export DEBUG=True
export IS_LOCAL=True
export BK_APIGW_NAME="demo"
export BK_API_URL_TMPL=http://bkapi.example.com/api/{api_name}/
export BKPAAS_APP_ID="demo"
export BKPAAS_APP_SECRET=358622d8-d3e7-4522-8f16-b5530776bbb8
export BKPAAS_DEFAULT_PREALLOCATED_URLS='{"dev": "http://0.0.0.0:8080/"}'
export BKPAAS_ENVIRONMENT=dev
export BKPAAS_PROCESS_TYPE=web
```

### Execute startup command (after execution, you can access: swagger ui address: http://0.0.0.0:8080/api/schema/swagger-ui/#/open )

### Reference [Development Guide]({{dev_guideline_url}}) to develop API, you can generate definition.yaml and resources.yaml locally for testing

```bash
python manage.py generate_definition_yaml && cat definition.yaml
python manage.py generate_resources_yaml && cat resources.yaml
```

### In the "Environment Overview" page, publish the resource to the corresponding environment

### In the "Resource Version" page, generate the SDK for the version published to the prod environment

{% endif %}