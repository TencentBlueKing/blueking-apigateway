# SDK Worker Deployment

The SDK generator runs in the dedicated `apigateway-dashboard-sdk-worker` image. It starts with `/app/bin/start_sdk_worker.sh` and consumes only the `sdk.generate` queue. Ordinary Dashboard and Celery workers must not subscribe to this queue.

Set `BK_APIGW_SDK_CELERY_QUEUE` (default `sdk.generate`) and `BK_APIGW_SDK_WORKER_CONCURRENCY` (default `2`). The worker shares the Dashboard database, Redis broker, encryption settings, BKRepo Generic credentials, and optional PyPI/Maven repository configuration. SDK naming and generation options use the `BK_SDK_LANGUAGES`, `SDK_SERVER_URL_TEMPLATE`, `SDK_PYTHON_*`, `SDK_JAVA_*`, `SDK_GO_MODULE_PREFIX`, `SDK_JAVASCRIPT_PACKAGE_SCOPE`, and `SDK_RUST_*` variables.

The pod needs outbound access to BKRepo and, when enabled, PyPI and Maven repositories. Toolchain builds may also resolve ecosystem dependencies through configured mirrors. Start with 100m CPU and 512Mi memory requests, 2 CPU and 4Gi memory limits, and 5Gi/20Gi ephemeral-storage request/limit. Increase temporary storage for unusually large OpenAPI documents or generated dependency trees.

Verify an image with `make test-sdk-worker-tools name=<image>` and `make test-sdk-worker-smoke name=<image>`. The Helm chart consumes this contract through `dashboard.sdkWorker` and `dashboard.sdkGeneration` in the `bk-apigateway-1.23.x` chart; its Deployment template is `templates/dashboard/sdk-worker-deployment.yaml`.
