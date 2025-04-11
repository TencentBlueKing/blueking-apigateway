## 开发指引

{% if language == "python" %}

### 拉取代码到本地

```bash
git clone {{repo_url}}
```

### 设置环境变量

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

### 执行启动命令 (执行后可访问：swagger ui 地址：http://0.0.0.0:8080/api/schema/swagger-ui/#/open )

### 参考 [开发指南]({{dev_guideline_url}}) 开发 API，可以本地生成 definition.yaml 和 resources.yaml 进行测试

```bash
python manage.py generate_definition_yaml && cat definition.yaml
python manage.py generate_resources_yaml && cat resources.yaml
```

### 在“环境概览”页面中，将资源发布到对应的环境

### 在“资源版本”页面中，将发布到 prod 环境的版本生成 SDK

{% endif %}