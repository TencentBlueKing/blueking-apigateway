## 运行环境与依赖

- Node.js {{ sdk_runtime_requirements.javascript|cut:">=" }} 及以上版本。包通过 `engines.node` 声明最低版本；npm 默认可能只给出版本不兼容警告。
- 浏览器需支持 ES2015+、Promise、Fetch（含 Request、Response、Headers）、URL 和 URLSearchParams；表单或文件操作还需 FormData 和 Blob。
- SDK 不内置 polyfill，缺失上述能力时需由使用方提供。
- npm 包包含编译后的 JavaScript 和 TypeScript 类型声明；直接使用该包无需自行编译 TypeScript。

## 安装

从 BKRepo Generic 安装生成的 npm 包：

```shell
{% if install_command %}{{ install_command }}{% else %}npm install "<BKRepo Generic npm tgz 地址>"{% endif %}
```

## 使用生成的客户端

该包直接提供 OpenAPI Generator `typescript-fetch` 生成的 API。

{% include "api_sdk/zh-hans/javascript_sdk_usage_example.md" %}
