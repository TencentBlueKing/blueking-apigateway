# 本地开发

> 注意node版本需要10.10.0以上

#### 安装依赖包
```
npm install
```

#### 配置host
```
127.0.0.1 dev-apigw.example.com
```

#### 配置开发环境变量

编辑build/dev.env.js, 修改配置中涉及的域名

示例

```javascript
export default merge(prodEnv, {
    NODE_ENV: NODE_ENV,
    LOCAL_DEV_URL: JSON.stringify('http://dev-apigw.example.com'), // 本地运行的url
    LOCAL_DEV_PORT: JSON.stringify('5000'),  // 本地运行端口
    AJAX_MOCK_PARAM: JSON.stringify('mock-file'),
    DASHBOARD_URL: 'http://dev-apigw.example.com/backend', // 后端接口前缀
    APISUPPORT_URL: 'http://dev-apigw.example.com/backend/docs', // 文档地址前缀
    BK_LOGIN_SIGN_IN_URL: 'http://paas.example.com/login', // 跳转登录地址
    DASHBOARD_CSRF_COOKIE_NAME: 'bk_apigateway_csrftoken', // CSRF cookie名称
})

```

#### 启动服务
```
// 版本代号: ee 代表开源版本
npm run dev:ee
```

# 打包构建
```
// 版本代号: ee 代表开源版本
npm run build:ee
```
命令执行完成后在项目根目录生成dist目录，包括前端运行的js、css等资源

# 线上部署

#### 需要配置的环境变量

- BK_LOGIN_SIGN_IN_URL: 跳转登录地址，必填，例如：http://paas.example.com/login/
- DASHBOARD_URL：模块 dashboard 服务地址，必填，例如：http://apigw.example.com/backend
- DASHBOARD_FE_URL：模块 dashboard-front 服务地址，例如：http://apigw.example.com
- DASHBOARD_CSRF_COOKIE_NAME: 后端公共csrf cookie名称，必填，例如：bk_apigw_dashboard_csrftoken
- API_RESOURCE_URL_TMPL: 网关 API 访问地址模板，必填，例如：http://bkapi.example.com/api/{api_name}/{stage_name}/{resource_path}
- BK_COMPONENT_API_URL：蓝鲸组件API地址，例如：http://bkapi.example.com
- BK_DOCS_URL_PREFIX：帮助文档地址，必填，例如：https://bk.tencent.com/docs
- DEFAULT_TEST_APP_CODE：API网关的测试应用，例如：bk_apigw_test

#### 环境变量配置的途径

- 可以在打包构建时通过环境变量传入，最终会填充在static/runtime.js配置文件里
- 也可以在打包构建后，手动修改static/runtime.js配置文件
- 也可以在服务运行时通过环境变量传入，Node.js服务会将变量动态注入到程序入口文件里
