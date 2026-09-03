# SDK Worker Deployment

SDK generation uses one dedicated Celery queue and one all-toolchain worker image. The `apigateway-dashboard-sdk-worker` image contains the Python, Java/Maven, Go, JavaScript/Node, and OpenAPI Generator toolchains; it intentionally contains no Rust or Cargo. The worker consumes only `sdk.generate`. Ordinary Dashboard and Celery workers must not subscribe to that queue.

## Runtime configuration

The Web/API processes and the SDK worker must receive the same generation policy:

- `SDK_GENERATION_ENABLED`: global switch for accepting new generation requests. Keep it `false` until the deployment gate below is complete.
- `BK_SDK_LANGUAGES`: comma-separated enabled subset of `python,java,go,javascript`.
- `BK_APIGW_SDK_CELERY_QUEUE`: dedicated queue name; defaults to `sdk.generate` and must match the queue consumed by the worker.
- `SDK_GENERATION_RETRY_DELAYS`: exactly two positive retry delays in seconds; defaults to `30,120`.
- `SDK_SERVER_URL_TEMPLATE`: generated client server URL template containing `{gateway_name}` and `{stage_name}`.
- `SDK_PYTHON_DISTRIBUTION_PREFIX`, `SDK_JAVA_GROUP_ID`, `SDK_JAVA_PACKAGE_PREFIX`, `SDK_GO_MODULE_PREFIX`, and `SDK_JAVASCRIPT_PACKAGE_SCOPE`: fixed package namespaces.
- `SDK_GENERIC_RETENTION_HOURS`, `SDK_SUBPROCESS_TIMEOUT_SECONDS`, `SDK_MAX_OPENAPI_BYTES`, `SDK_MAX_OUTPUT_BYTES`, and `SDK_MAX_ARTIFACT_BYTES`: retention and worker resource limits.
- `SDK_OPENAPI_GENERATOR_JAR`, `SDK_OPENAPI_GENERATOR_VERSION`, and `SDK_WORKER_LOCK_FILE`: immutable generator and toolchain identity inputs. Image defaults point to the files baked into the worker image.

The worker process also accepts `BK_APIGW_SDK_WORKER_CONCURRENCY` (default `2`). Start with 100m CPU and 512Mi memory requests, 2 CPU and 4Gi memory limits, and 5Gi/20Gi ephemeral-storage request/limit. Increase temporary storage for unusually large OpenAPI documents or generated dependency trees.

BKRepo Generic is mandatory for every generated language. Configure `BKREPO_ENDPOINT_URL`, `BKREPO_USERNAME`, `BKREPO_PASSWORD`, `BKREPO_PROJECT`, and `BKREPO_GENERIC_BUCKET`. The pod needs outbound access to that repository and to dependency mirrors used during package builds.

Python and Java native publication is optional and independent from Generic publication:

- PyPI: `DEFAULT_PYPI_REPOSITORY_URL`, `DEFAULT_PYPI_INDEX_URL`, `DEFAULT_PYPI_USERNAME`, and `DEFAULT_PYPI_PASSWORD`.
- Maven: `DEFAULT_MAVEN_REPOSITORY_URL`, `DEFAULT_MAVEN_REPOSITORY_ID`, `DEFAULT_MAVEN_USERNAME`, `DEFAULT_MAVEN_PASSWORD`, `DEFAULT_MAVEN_SSL_INSECURE`, and `DEFAULT_MAVEN_MIRROR_URL`.

## Startup and readiness

`/app/bin/start_sdk_worker.sh` loads the Dashboard environment file and runs `python manage.py validate_sdk_worker` before starting Celery. Validation checks the required Generic configuration, lock-file shape, generator checksum/version, and installed toolchain versions. An invalid configuration or image exits before the process can claim a task.

The chart's readiness check must stay false until startup validation has succeeded and the Celery worker process is running on the configured dedicated queue. Repository reachability and credentials must be exercised by deployment checks; startup validation and the image smoke test do not publish to remote repositories.

Verify each edition image before rollout:

```shell
make test-sdk-worker-tools name=<image>
make test-sdk-worker-smoke name=<image>
```

The tool gate verifies the pinned toolchain and the absence of `rustc` and `cargo`. The smoke gate generates and builds all four SDKs, installs or references each artifact from a clean consumer project, and constructs a generated API client without calling a live gateway.

## Upgrade and enablement

Use this order for a deployment:

1. Set `SDK_GENERATION_ENABLED=false` on Web/API processes so no new work is enqueued.
2. Stop the existing SDK workers after currently claimed items finish.
3. Apply migration `0019_sdk_generation_tasks`.
4. Deploy the new Web/API image and the all-toolchain SDK worker image.
5. Run application health checks, both edition image tool/smoke gates, API contract tests, and frontend gates; confirm the SDK worker is ready on the dedicated queue.
6. Set `SDK_GENERATION_ENABLED=true` once, only after all preceding gates succeed.

Do not enable generation separately during partial rollouts. The API and worker must share the same language, naming, retry, queue, and repository configuration.

## Rollback

First set `SDK_GENERATION_ENABLED=false`. This stops new enqueueing without disabling SDK list, task-detail, or download reads. Let already claimed items finish, then stop or roll back the SDK workers. Unclaimed queued items remain pending and resume when a compatible worker is deployed and generation is re-enabled. Never route pending or new requests to the legacy generator.

Keep the generation records and Generic artifacts during rollback; they are the durable source for later resume and download. Native PyPI/Maven failures remain separate and do not invalidate a successful Generic artifact.

The Helm values, Deployment, queue routing, readiness probe, resources, and rollout ordering are implemented in the external chart repository as a separately reviewed change. This repository defines the application/image contract only; publishing this code does not imply that chart change has been applied.
