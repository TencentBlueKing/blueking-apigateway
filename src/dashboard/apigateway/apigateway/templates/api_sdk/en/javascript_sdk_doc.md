## Runtime requirements and dependencies

- Node.js {{ sdk_runtime_requirements.javascript|cut:">=" }} or later. The package declares this minimum in `engines.node`; npm may only warn about incompatible versions by default.
- Browsers must support ES2015+, Promise, Fetch (including Request, Response and Headers), URL and URLSearchParams. Form and file operations also require FormData and Blob.
- No polyfills are bundled; consumers must provide compatible polyfills for missing APIs.
- The npm package includes compiled JavaScript and TypeScript declarations. Consumers do not need to compile TypeScript to use it.

## Install

Install the generated npm package archive from BKRepo Generic:

```shell
{% if install_command %}{{ install_command }}{% else %}npm install "<BKRepo Generic npm tgz URL>"{% endif %}
```

## Use the generated client

The package exposes the native OpenAPI Generator `typescript-fetch` API.

{% include "api_sdk/en/javascript_sdk_usage_example.md" %}
