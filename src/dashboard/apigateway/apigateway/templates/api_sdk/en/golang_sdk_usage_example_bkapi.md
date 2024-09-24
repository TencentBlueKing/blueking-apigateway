
Create a gateway {{gateway_name}} Client and call the API resource {{resource_name}} Usage Examples
### Naming conventions:

The following naming conventions are used in the bkapi package:

| Patterns | Types | Meaning | Reference Documents |
| --------------------- | ---- | --------------------------------------- | --------- |
| bkapi. Opt * | Functions | Options that can work on both Client and Operation | option.go |
| bkapi. * BodyProvider | Structure | Interface that provides request body serialization encapsulation | json.go |
| bkapi. * ResultProvider | Structure | Interface to provide response body deserialization encapsulation | json.go |

### Use the `bkapi` base library for `bk-apigateway-sdks` directly.

```golang
package demo

import (
	“fmt”
	“log”

	“github.com/TencentBlueKing/bk-apigateway-sdks/core/bkapi”
	“github.com/TencentBlueKing/bk-apigateway-sdks/core/define”
)

type QueryUserDemoBodyRequest struct {
	Name string `json: “name”`
	Age int `json: “age”`
}

type QueryUserDemoResponse struct {
	Name string `json: “name”`
	Age int `json: “age”`
	Address string `json: “address”`
	Gender string `json: “gender”`
}

func clientExample() {

	// Initialize the client

	client, err := bkapi.NewBkApiClient(“demo”, bkapi.ClientConfig{
		Endpoint: “http://special-api.example.com/prod”,// a specific gateway address
		ClientOptions: []define.BkApiClientOption{
			// Set some general client configuration, eg. 
			bkapi.OptSetRequestHeader(“X-Api-Key”, “123456”),// set the uniform header
			bkapi.OptJsonResultProvider(),// Declare all responses from this gateway to be JSON
			bkapi.OptJsonBodyProvider(), // Declare that all body requests from this gateway are JSON.
		}, })
	})
	if err ! = nil {
		log.Printf(“client init error: %v”, err)
		log.Printf(“client init error: %v”, err)
	}



	// Create the api operation
	apiOperation := client.NewOperation(
		// Fill in the interface configuration
		bkapi.OperationConfig{
			Name: “query_team_user_demo”,
			Method: “GET”,
			Path: “/get/{team_id}/user/”,
		}, // Set the header parameter. 
		// Set the header parameter 
		bkapi.OptSetRequestHeader(“X-Bkapi-Header”, “demo”),
		// Set the path parameter
		bkapi.OptSetRequestPathParams(
			map[string]string{
				“team_id": `1`,, // Set the path parameters.
			},
		), // Set the query parameters.
		// Set the query parameters
		bkapi.OptSetRequestQueryParam(“name”, “demo”), // set the body parameter: customize the constructor.
		// Set the body parameter: custom struct
		bkapi.OptSetRequestBody(QueryUserDemoBodyRequest{Name: “demo”}), // set the body parameter: map[map], “demo”, // set the body parameter.
		// Set the body parameter: map[string]string
		bkapi.OptSetRequestBody(map[string]string{“name”: “demo”}), )
	)

	// Create the result variable
	var result QueryUserDemoResponse

	// Call the interface (Request() returns: *http.Response,err, depending on the case if it needs to be handled)

	//// pass the parameter directly through the api operation
	//_,_=apiOperation.SetHeaders(map[string]string{“X-Bkapi-Header”: “demo”}).
	// SetPathParams(map[string]string{“team_id”: `1`}).
	// SetBody(QueryUserDemoBodyRequest{Name: “demo”}).
	// SetQueryParams(map[string]string{“name”: “demo”}).
	// SetResult(&result).Request()

	//_, _ = client.StatusCode(bkapi.OptSetRequestQueryParams(map[string]string{
	// “code”: `200`, //})).SetResults(bkapi.
	//})).SetResult(&result).Request()

	_, _ = apiOperation.SetResult(&result).Request()
	// The result will be automatically populated into result
	fmt.Printf(“%#v”, result)

}
```

### Download generated gateway sdk `bkapi-{{gateway_name}}-{{sdk_version}}`

Contents of the generated sdk

```golang

package {{gateway_name}}

import (
	"github.com/TencentBlueKing/bk-apgateway-sdks/core/bkapi"
	"github.com/TencentBlueKing/bk-apigateway-sdks/core/define"
)

// VERSION for resource definitions
const VERSION = “{{sdk_version}}”

// Client for bkapi {{gateway_name_with_underscore}}
type Client struct {
	define.BkApiClient
}

// New {{gateway_name_with_underscore}} client
func New(configProvider define.ClientConfigProvider, opts . .define.BkApiClientOption) (*Client, error) {
	client, err := bkapi.NewBkApiClient(“httpbin”, configProvider, opts ...)
	if err ! = nil {
		return nil, err
	}

	return &Client{BkApiClient: client}, nil
}


// {{resource_name}} for bkapi resource {{resource_name}}
// Returns anything passed in request data.
func (c *Client) {{resource_name}} (opts ... .define.OperationOption) define.Operation {
	return c.BkApiClient.NewOperation(bkapi.OperationConfig{
		Name: “{{resource_name}}”,
		Method: “{{method}}”,
		Path: “xxxx/xxxx”, }, opts...
	}, opts...)
}

```

## Advanced Usage

### Enable logging

The logging implementation can be passed in via the `Logger` property of `bkapi.ClientConfig` to capture relevant running logs and error messages to assist in troubleshooting.
When this property is empty, the logging implementation named *github.com/TencentBlueKing/bk-apigateway-sdks/core/bkapi* will be fetched by default.
The log output will take the Context corresponding to the request with it, which can be used in conjunction with OTLP to improve link observability.
See [github.com/TencentBlueKing/gopkg/logging](https://github.com/TencentBlueKing/gopkg/tree/master/logging) for details.

### Configuration Center
You can use `ClientConfigRegistry` to simplify the repetitive work of passing gateway address, authentication information, etc. every time you initialize a client. `ClientConfigRegistry` itself has been implemented as a `ClientConfigProvider`, which can be used as a direct replacement for `ClientConfig` to to be used directly instead of `ClientConfig`:

```golang
// Initialize the client through the ClientConfigRegistry.

// Initialize the client using the default global configuration center
registry: = bkapi.GetGlobalClientConfigRegistry()

// Way 1: register the default configuration (regardless of gateway)
err: = registry.RegisterDefaultConfig(bkapi.ClientConfig {
        BkApiUrlTmpl: “http://{api_name}.example.com/”, // gateway generic address
        Stage: “prod”, //Configure.ClientConfig
})
if err ! = nil {
        log.Printf(“registry default config error: %v”, err)
        log.Printf(“registry default config error: %v”, err)
}
// Use the default configuration and specify the gateway when creating the client
client, err: = bkapi.NewBkApiClient(“my-gateway”, registry)
if err ! = nil {
        log.Fatalf(“create bkapi client error: %v”, err)
        return
}



// Method 2: Register the specified gateway configuration
err = registry.RegisterClientConfig(“my-gateway”, bkapi.ClientConfig {
        Endpoint: “http://special-api.example.com/prod”, // a specific gateway address
        ClientOptions: [] define.BkApiClientOption {
        // Set some general client configuration, eg. 
        bkapi.OptSetRequestHeader(“X-Api-Key”, “123456”), // set the uniform header
        bkapi.OptJsonResultProvider(), // Declare all responses from this gateway to be JSON
        bkapi.OptJsonBodyProvider(), // Declare that all body requests for this gateway are JSON
       }, })
    })

if err ! = nil {
        log.Fatalf(“set bkapi client config error: %v”, err)
        if err != nil { log.
}


client, err = bkapi.NewBkApiClient(“my-gateway”, registry)
NewBkApiClient(“my-gateway”, registry) if err ! = nil {
        log.Fatalf(“create bkapi client error: %v”, err)
        log.Fatalf(“create bkapi client error: %v”, err)
}
```

### Prometheus metrics
 

The *github.com/prometheus/client_golang/prometheus* module implements the Prometheus plugin, which, when enabled, allows for metrics to be counted during a request:

```golang
// Enable the metrics plugin with the metrics prefix
prometheus.Enable(prometheus.PrometheusOptions{
	Namespace: “project”,
	Subsystem: “module”, })
})
```



Indicators at a glance:


| Name | Type | What it does |
| ------------------------------- | --------- | -------- |
| bkapi_requests_duration_seconds | Histogram | Request duration |
| bkapi_requests_body_bytes | Histogram | Request size |
| bkapi_responses_body_bytes | Histogram | Response size |
| bkapi_responses_total | Counter | Response Count |
| bkapi_failures_total | Counter | Number of failures |

## Definition Description
### Resource encapsulation

Operation represents a gateway resource wrapper, method definition:

| Methods | Usage |
| ----------------- | ------------------------------------------------ |
| SetHeaders | Set request headers |
| SetQueryParams | Set request parameters (querystring) |
| SetPathParams | Set path variables |
| | SetBodyReader | Set request content (`io.Reader`) |
| | SetBody | Set request parameters (to be handled by the request parameter serializer) |
| SetBodyProvider | Set the request parameter serializer (with `SetBody`) |
| SetResult | Set the response structure (to be handled by the response serializer) |
| | SetResultProvider | Set the response serializer (with `SetResult`) |
| SetContext | Set the request context | | SetContentType | | SetContactType
| | SetContentType | Sets the request `Content-Type` header, which is available to custom serializers |
| SetContentLength | Set the request `Content-Length` header, available to custom serializers |
| Apply | Add additional options | | Request | Send a request.
| Request | Send Request |


```golang
// Create the api operation
apiOperation := client.NewOperation(
    // Fill in the interface configuration
    bkapi.OperationConfig{
        Name: “query_team_user_demo”,
        Method: “GET”,
        Path: “/get/{team_id}/user/”,
    }, // Set the header parameter.
    // Set the header parameter
    bkapi.OptSetRequestHeader(“X-Bkapi-Header”, “demo”),
    // Set the path parameter
    bkapi.OptSetRequestPathParams(
        map[string]string{
        “team_id": `1`,, // Set the path parameters.
        },
    ), // Set the query parameters.
    // Set the query parameters
    bkapi.OptSetRequestQueryParam(“name”, “demo”), // set the body parameter: customize the constructor.
    // Set the body parameter: custom struct
    bkapi.OptSetRequestBody(QueryUserDemoBodyRequest{Name: “demo”}), // set the body parameter: map[map], “demo”, // set the body parameter.
    // Set the body parameter: map[string]string
    bkapi.OptSetRequestBody(map[string]string{“name”: “demo”}), )
)

// Create the result variable
var result QueryUserDemoResponse

// Call the interface (Request() returns: *http.Response,err, depending on the case if it needs to be handled)

//// pass the parameter directly through the api operation
//_,_=apiOperation.SetHeaders(map[string]string{“X-Bkapi-Header”: “demo”}).
// SetPathParams(map[string]string{“team_id”: `1`}).
// SetBody(QueryUserDemoBodyRequest{Name: “demo”}).
// SetQueryParams(map[string]string{“name”: “demo”}).
// SetResult(&result).Request()

_, _ = apiOperation.SetResult(&result).Request()
// The result will be automatically populated into result
fmt.Printf(“%#v”, result)
```

### Client wrappers

BkApiClient represents a gateway wrapper, method definition:

| Methods | Usage |
| ------------------- | ------------------------------------ |
| Apply | Add additional options (for BkApiClient) |
| AddOperationOptions | Add resource generic options (for Operation) |
| | AddOperationOptions | Add Resource Generic Options (acts on Operation) | | NewOperation | Creates the associated resource wrapper and applies the generic options |

### Client configuration
The client configuration is passed in through the `bkapi.ClientConfig` type, and some parameters are automatically filled in:

| Field | Type | Meaning | Required | Default rule |
| ------------------- | -------------------------- | -------------- | ---- | ------------------------------------------------------------------------------- |
| Endpoint | string | Base address | Yes | `"{BkApiUrlTmpl}/{Stage}"` |
| BkApiUrlTmpl | string | Gateway address template | No | Environment variable `BK_API_URL_TMPL` |
| Stage | string | Environment name | No | `"prod"` |
| AppCode | string | Application code | No | Environment variable `BK_APP_CODE` |
| AppSecret | string | Application name | No | Environment variable `BK_APP_SECRET` |
| AccessToken | string | Access token | No | |
| AuthorizationParams | string | Additional authentication parameters | No | |
| Logger | logging.Logger | Log implementation | No | `logging.GetLogger("github.com/TencentBlueKing/bk-apigateway-sdks/core/bkapi")` |
| ClientOptions | []define.BkApiClientOption | General client options | No | |

Note that you can choose one configuration method between Endpoint and BkApiUrlTmpl/Stage, and the latter is recommended.