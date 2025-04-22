## 开发指引

{% if language == "python" %}

### 1. 初始化项目

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
git remote add origin https://example.com/{{project_name}}.git # 请替换为实际的仓库地址
git push -u origin master
{% else %}
git clone {{repo_url}}
{% endif %}
```

### 2. 本地开发：设置环境变量

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

### 3. 执行启动命令 (执行后可访问：swagger ui 地址：http://0.0.0.0:8080/api/schema/swagger-ui/#/open )

```bash
python manage.py runserver 0.0.0.0:8080
```

### 4. 参考 [开发指南]({{dev_guideline_url}}) 开发 API，可以本地生成 definition.yaml 和 resources.yaml 进行测试

```bash
python manage.py generate_definition_yaml && cat definition.yaml
python manage.py generate_resources_yaml && cat resources.yaml
```

### 5. 在“环境概览”页面中，将资源发布到对应的环境

### 6. 在“资源版本”页面中，将发布到 prod 环境的版本生成 SDK

{% endif %}