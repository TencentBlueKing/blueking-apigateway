## Development Guide

{% if language == "python" %}

### 1. Initialize the Project

```bash
{% if edition == "ee" %}
pip install cookiecutter

cookiecutter https://github.com/TencentBlueKing/bk-apigateway-framework/ --directory templates/python
project_name: {{project_name}}
init_admin: {{init_admin}}

cd {{project_name}}
git init
git add .
git commit -m "init project"
git remote add origin {{repo_url}} # Replace with the actual repository URL
git push -u origin master
{% else %}
git clone {{repo_url}}
{% endif %}
```

### 2. Local Development: Set Environment Variables

```bash
export DEBUG=True
export IS_LOCAL=True
export BK_APIGW_NAME={{project_name}}
export BK_API_URL_TMPL={{bk_api_url_tmple}}
export BKPAAS_APP_ID={{project_name}}
export BKPAAS_APP_SECRET=358622d8-d3e7-4522-8f16-b5530776bbb8 ## Replace with the actual BKPAAS_APP_SECRET
export BKPAAS_DEFAULT_PREALLOCATED_URLS='{"dev": "http://0.0.0.0:8080/"}'
export BKPAAS_ENVIRONMENT=dev
export BKPAAS_PROCESS_TYPE=web
```

### 3. Execute the Start Command (After execution, you can access: swagger ui URL: http://0.0.0.0:8080/api/schema/swagger-ui/#/open)

```bash
python manage.py runserver 0.0.0.0:8080
```

### 4. Refer to the [Development Guide]({{dev_guideline_url}}) to develop APIs. You can locally generate definition.yaml and resources.yaml for testing.

```bash
python manage.py generate_definition_yaml && cat definition.yaml
python manage.py generate_resources_yaml && cat resources.yaml
```

### 5. Publish the resources to the corresponding environment on the "Environment Overview" page.

### 6. Generate the SDK for the version published to the prod environment on the "Resource Version" page.

{% endif %}

{% if language == "go" %}
### 1. Initialize the Project

```bash
{% if edition == "ee" %}
pip install cookiecutter

cookiecutter https://github.com/TencentBlueKing/bk-apigateway-framework/ --directory templates/golang
project_name: {{project_name}}
init_admin: {{init_admin}}

cd {{project_name}}
git init
git add .
git commit -m "init project"
git remote add origin {{repo_url}} # Replace with the actual repository URL
git push -u origin master
{% else %}
git clone {{repo_url}}
{% endif %}
```

### 2. Local Development: Set Environment Variables

Set environment variables (You can create a new `.envrc` file in the project root path and place the following content in it, which will be automatically loaded upon startup; or you can manually execute the following content in the startup command line terminal.)

```bash
export DEBUG=True
export IS_LOCAL=True
export BK_APIGW_NAME={{project_name}}
export BK_API_URL_TMPL={{bk_api_url_tmple}}
export BKPAAS_APP_ID={{project_name}}
export BKPAAS_APP_SECRET=358622d8-d3e7-4522-8f16-b5530776bbb8 ## Replace with the actual BKPAAS_APP_SECRET
export BKPAAS_DEFAULT_PREALLOCATED_URLS='{"dev": "http://0.0.0.0:8080/"}'
export BKPAAS_ENVIRONMENT=dev
export BKPAAS_PROCESS_TYPE=web
```


### 3. Execute the Start Command (After execution, you can access: swagger ui URL: http://0.0.0.0:8080/swagger-ui/index.html)

```bash
 go run main.go webserver
```


### 4. Refer to the [Development Guide]({{dev_guideline_url}}) to develop APIs. You can locally generate definition.yaml and resources.yaml for testing.

```bash
go run main.go  generate_definition_yaml && cat definition.yaml
go run main.go  generate_resources_yaml && cat resources.yaml
```

### 5. Publish the resources to the corresponding environment on the "Environment Overview" page.

### 6. Generate the SDK for the version published to the prod environment on the "Resource Version" page.

{% endif %}