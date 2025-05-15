# Gateway Error Response Explanation

## Pre-Explanation

> Link: Caller -> APIGateway -> Backend Service

The current gateway error response protocol is

```json
{
  "code_name": "",
  "data": null,
  "code": 16xxxxx,
  "message": "",
  "result": false
}
```

If the response body does not follow this protocol, then the response is returned by the `backend service`. If there are questions about the response, please contact the corresponding **gateway responsible person**.

The following is a detailed explanation of the gateway's error responses. You can search by status code or keyword.

## status: 400

### app code cannot be empty

```json
{
  "code": 1640001,
  "data": null,
  "code_name": "INVALID_ARGS",
  "message": "Parameters error [reason=\"app code cannot be empty\"]",
  "result": false
}
```

- Reason: The `X-Bkapi-Authorization` header is not provided, or the `X-Bkapi-Authorization` header does not contain `bk_app_code`.
- Solution: Provide the `X-Bkapi-Authorization` header and include `bk_app_code` in it.

Others:
- `app code cannot be longer than 32 characters`: The passed `bk_app_code` is incorrect. Normally issued `bk_app_code` will not exceed 32 characters.
- `app secret cannot be longer than 128 characters`: The passed `bk_app_secret` is incorrect. Normally issued `bk_app_secret` will not exceed 128 characters.

### please provide bk_app_secret or bk_signature to verify app

```json
{
  "code": 1640001,
  "data": null,
  "code_name": "INVALID_ARGS",
  "message": "Parameters error [reason=\"please provide bk_app_secret or bk_signature to verify app\"]",
  "result": false
}
```

- Reason: The `X-Bkapi-Authorization` header does not contain `bk_app_secret`.
- Solution: Include `bk_app_secret` in the `X-Bkapi-Authorization` header.

### bk_app_code or bk_app_secret is incorrect

```json
{
  "code": 1640001,
  "data": null,
  "code_name": "INVALID_ARGS",
  "message": "Parameters error [reason=\"bk_app_code or bk_app_secret is incorrect\"]",
  "result": false
}
```

- Reason: The `bk_app_code + bk_app_secret` verification failed, it is invalid.
- Solution: Ensure that the `bk_app_code / bk_app_secret` in the request header is valid and matches the one issued by the BlueKing PaaS platform or operation and maintenance.

### user authentication failed, please provide a valid user identity, such as bk_username, bk_token, access_token

```json
{
  "code": 1640001,
  "data": null,
  "code_name": "INVALID_ARGS",
  "message": "Parameters error [reason=\"user authentication failed, please provide a valid user identity, such as bk_username, bk_token, access_token\"]",
  "result": false
}
```

- Reason:
    - The `X-Bkapi-Authorization` header is not provided.
    - The header does not contain `bk_token` or `access_token`.
    - `bk_token` is invalid (it will be verified by BlueKing unified login, and the verification failed, possibly due to an illegal `bk_token` or it has expired).
    - `access_token` is invalid (it will be verified by BlueKing bkauth/ssm, and the verification failed, possibly due to an illegal `access_token` or it has expired).
- Solution: Ensure that `bk_token/access_token` exists and is valid.

### user authentication failed, the user indicated by bk_username is not verified

```json
{
    "code":1640001,
    "data":null,
    "code_name":"INVALID_ARGS",
    "message":"Parameters error [reason=\"user authentication failed, the user indicated by bk_username is not verified\"]",
    "result":false
}
```

- Reason:
  - The provided user authentication information only contains `bk_username`, without `bk_token`, `access_token`, or other information that can represent the user's real identity. `bk_username` cannot truly represent the user's real identity (not verified).
- Solution:
  - Provide a valid `bk_token/access_token`.

Others:
In the gateway "plugin configuration", find the plugin "User Authentication Exemption Whitelist (Not Recommended)", and add the application to the whitelist in the plugin configuration. This plugin is not recommended, and unofficial gateways may not be able to add this plugin.

Note: The `User Authentication Exemption Whitelist (Not Recommended)` will be discontinued. It is not recommended to use this plugin. The interface should enable `application authentication` or `user authentication` according to requirements, and should not disable `user authentication` and then try to obtain user information.

### access_token is invalid

```json
{
    "code":1640001,
    "data":null,
    "code_name":"INVALID_ARGS",
    "message":"Parameters error [reason=\"access_token is invalid, url: ......., code: 403\"]",
    "result":false
}
```

- Reason:
  - The `access_token` is incorrect, possibly copied wrong.
  - The `access_token` has expired.
  - The `access_token` was not generated through [bkssm or bkauth](https://bk.tencent.com/docs/markdown/EN/APIGateway/1.14/UserGuide/Explanation/access-token.md) or is from another environment.
- Solution:
  - If it has expired, you can renew it or generate a new `access_token` [access_token API documentation](https://bk.tencent.com/docs/markdown/EN/APIGateway/1.14/UserGuide/Explanation/access-token.md).

### the access_token is the application type and cannot indicate the user

```json
{
    "code_name": "INVALID_ARGS",
    "code": 1640001,
    "data": null,
    "message": "Parameters error [reason=\"the access_token is the application type and cannot indicate the user\"]",
    "result": false
}
```

- Reason:
  - The `access_token` used to call the API is of the application type, which only represents `bk_app_code+bk_app_secret` and cannot represent the user.
- Solution:
  - Apply for and use a user-type `access_token` to call the interface 165040.

## status: 401

## status: 403

### App has no permission to the resource

```
{
  "code": 1640301,
  "data": null,
  "code_name": "APP_NO_PERMISSION",
  "message": "App has no permission to the resource",
  "result": false
}
```

- Reason: The gateway API has enabled `access permission verification`, and the caller `bk_app_code` does not have permission to call (no permission has been applied for or the permission has expired).
- Solution: Go to the Developer Center, find the corresponding application, click in, and apply for the corresponding interface permission or renew the permission under `Cloud API Management - Cloud API Permissions`.

### Request rejected by ip restriction

```json
{
  "code_name": "IP_NOT_ALLOWED",
  "message": "Request rejected by ip restriction",
  "result": false,
  "data": null,
  "code": 1640302
}
```

- Reason: Triggered the IP access protection configured by the gateway or resource.
- Solution: Add the caller's IP to the IP access protection whitelist.

## status: 404

### API not found

```json
{
  "code_name": "API_NOT_FOUND",
  "message": "API not found [method=\"POST\" path=\"/api/xxxxx\"]",
  "result": false,
  "data": null,
  "code": 1640401
}
```

- Reason: The corresponding API (method+path) cannot be found in APIGateway.
- Solution:
  - The caller confirms that the called method / path is correct and not spliced incorrectly.
  - Contact the gateway responsible person to confirm that the corresponding method / path resource has been released and the interface exists.

## status: 413

### Request body size too large

```json
{
  "code_name": "BODY_SIZE_LIMIT_EXCEED",
  "message": "Request body size too large.",
  "result": false,
  "data": null,
  "code": 1641301
}
```

- Reason: The request body exceeds the gateway limit. The current gateway limit is 40M.
- Solution:
   - Do not go through the gateway, directly request the backend service.

## status: 414

### Request uri size too large

```json
{
  "code_name": "URI_SIZE_LIMIT_EXCEED",
  "message": "Request uri size too large.",
  "result": false,
  "data": null,
  "code": 1641401
}
```

- Reason: The request uri exceeds the gateway limit.
- Solution:
   - Do not place excessively long parameters in the uri.

## status: 415

The gateway will not return `status code = 415`. For details, refer to [How to confirm whether the error response is returned by the gateway or the backend service? - Backend returns status code 415](https://bk.tencent.com/docs/markdown/EN/APIGateway/1.14/UserGuide/FAQ/gateway-error-or-backend-error.md).

## status: 429

### API rate limit exceeded by stage strategy

```json
{
  "code_name": "RATE_LIMIT_RESTRICTION",
  "message": "API rate limit exceeded by stage strategy",
  "result": false,
  "data": null,
  "code": 1642902
}
```

- Reason: The application triggered the access frequency control strategy of the corresponding `environment` of the gateway.
- Solution: Reduce the call frequency, or contact the gateway responsible person to adjust the corresponding frequency limit.

You can obtain access frequency control related information from the request header.

```
"X-Bkapi-RateLimit-Limit": Total frequency control count
"X-Bkapi-RateLimit-Remaining": Remaining count
"X-Bkapi-RateLimit-Reset": Time until reset
"X-Bkapi-RateLimit-Plugin": Plugin name
```

### API rate limit exceeded by resource strategy

```json
{
  "code_name": "RATE_LIMIT_RESTRICTION",
  "message": "API rate limit exceeded by resource strategy",
  "result": false,
  "data": null,
  "code": 1642903
}
```

- Reason: The application call triggered the access frequency control strategy of the corresponding `API resource` of the gateway.
- Solution: Reduce the call frequency, or contact the gateway responsible person to adjust the corresponding frequency limit.

You can obtain access frequency control related information from the request header.

```
"X-Bkapi-RateLimit-Limit": Total frequency control count
"X-Bkapi-RateLimit-Remaining": Remaining count
"X-Bkapi-RateLimit-Reset": Time until reset
"X-Bkapi-RateLimit-Plugin": Plugin name
```

### API rate limit exceeded by stage global limit (deprecated)

```json
{
  "code_name": "RATE_LIMIT_RESTRICTION",
  "message": "API rate limit exceeded by stage global limit",
  "result": false,
  "data": null,
  "code": 1642901
}
```

- Reason: The application triggered the global access frequency control strategy of the corresponding `environment` of the gateway (deprecated).
- Solution: Reduce the call frequency, or contact the gateway responsible person to adjust the corresponding frequency limit.

(Deprecated, most environments should not have this plugin strategy.)

### Request concurrency exceeds

```json
{
  "code_name": "CONCURRENCY_LIMIT_RESTRICTION",
  "message": "Request concurrency exceeds",
  "result": false,
  "data": null,
  "code": 1642904
}
```

- Reason: The request concurrency is too high, exceeding the gateway limit.
- Solution: Reduce the concurrency (Note: It is prohibited to use the gateway interface for stress testing).INTERNAL_SERVER_ERROR

## status: 499 Client Closed Request

### No response body

> 499 client has closed connection indicates that the **client** disconnected, meaning the client initiated a request but closed the connection before receiving a response from the server.

Reason: The client's call to the gateway exceeded the set timeout time, and the client actively closed the connection. This may be due to the client setting the timeout too short, or the backend service responding very slowly.

Solution:
  - Confirm whether the client's timeout setting is reasonable.
  - Contact the gateway responsible person to confirm whether the backend service's performance meets the requirements (you can reduce the backend service's response time through interface performance optimization, capacity expansion, etc.).

Other phenomena and reasons:
- The user's application requests the gateway or ESB interface, the request fails, and the gateway log shows a status code of 499.
  - If it is a SaaS, and the failed requests are mostly around 30s, please check if it is started with gunicorn. If the timeout is not configured, the default is `30s` [gunicorn settings timeout](https://docs.gunicorn.org/en/stable/settings.html#timeout).
  - If it is not a SaaS, then you need to check the context of the request initiation, whether it is in a certain worker or handler, which will cause the request to be aborted due to the worker or handler being aborted.

## status: 500

## status: 502

### cannot read header from upstream

```json
{
  "data": null,
  "code_name": "BAD_GATEWAY",
  "code": 1650200,
  "message": "Bad Gateway [upstream_error=\"cannot read header from upstream\"]",
  "result": false
}
```

- The corresponding nginx error log is: `upstream prematurely closed connection while reading response header from upstream`, you can [google this string](https://www.google.com.hk/search?q=upstream+prematurely+closed+connection+while+reading+response+header+from+upstream&oq=upstream+prematurely+closed+connection+while+reading+response+header+from+upstream&sourceid=chrome&ie=UTF-8) for further understanding.

- Reason: The gateway requested the backend service, and while waiting for the backend service to respond, the connection was interrupted due to network reasons (e.g., jitter) or backend service reasons (e.g., reload, restart).
    - The backend has been released/restarted.
    - The backend has enabled keep-alive but the configured keep-alive timeout is less than 60s.

- Solution:
  - Provide the call information (time/request information/request-id, etc.) to the gateway responsible person to investigate the cause. Whether it is caused by release/restart, if not, the gateway responsible person needs to further investigate.

### DNS resolution failed

```json
{
  "data": null,
  "code_name": "BAD_GATEWAY",
  "code": 1650200,
  "message": "Bad Gateway",
  "result": false
}
```

When the domain address of the backend service that the gateway proxies to cannot be resolved by DNS, it will also manifest as 502. At this time, since the underlying resolution failure error is only logged in the nginx error.log, the upper-level plugin cannot obtain the specific error.

Common:
1. The backend service address is configured incorrectly.

Solution: You need to check whether the backend service address domain can be pinged in the IDC.

### Request backend service failed

```json
{
  "data": null,
  "code_name": "ERROR_REQUESTING_RESOURCE",
  "code": 1650201,
  "message": "Request backend service failed [detail=\"Bad Gateway\" err=\"EOF\" status=\"502\"]",
  "result": false
}
```

- Reason: The gateway failed to request the backend service. See the `message` for specific error information.
- Solution: Directly concatenate the backend service address and use `curl` to access and confirm the problem on the IDC machine. It is generally caused by the backend service or the backend service's access layer.

## status: 503

## status : 504

### cannot read header from upstream

```json
{
  "code_name": "REQUEST_BACKEND_TIMEOUT",
  "data": null,
  "code": 1650401,
  "message": "Request backend service timeout [upstream_error=\"cannot read header from upstream\"]",
  "result": false
}
```
- The corresponding nginx error log is: `upstream timed out (110: Connection timed out) while reading response header from upstream`, you can google this string for further understanding.

- Reason: The gateway resource will configure the timeout time of the backend interface. If the backend interface call times out, the gateway returns 504.
- Solution: The backend service needs to improve the interface performance (you can reduce the backend service's response time through interface performance optimization, capacity expansion, etc.), or increase the gateway's timeout time (not recommended to be too large).

Additional:
- Another possible reason: The backend service only supports https, not http protocol, and the backend address configured in the gateway environment uses `http://{host}:{port}`.
- Solution: Change the protocol to https `https://{host}:{port}`.

## status: 508

### Recursive request detected, please contact the api manager to check the resource configuration

```json
{
  "code_name": "RECURSIVE_REQUEST_DETECTED",
  "data": null,
  "code": 1650801,
  "message": "Recursive request detected, please contact the api manager to check the resource configuration",
  "result": false
}
```

- Reason: The gateway prohibits using another gateway as a backend, which may lead to infinite recursive calls and eventually cause the gateway service itself to crash, so detection is implemented.
- Solution:
  - Do not use another gateway address as a backend.
  - If the request comes from the gateway and reaches the backend service, and needs to call another gateway interface again, do not reuse the header of this request. Instead, you should create a new request, assemble the relevant information, and then initiate the call (reusing the upstream request header will bring security issues, and the downstream can obtain various information that does not belong to it, including user information/some sensitive information agreed by the system, etc.).