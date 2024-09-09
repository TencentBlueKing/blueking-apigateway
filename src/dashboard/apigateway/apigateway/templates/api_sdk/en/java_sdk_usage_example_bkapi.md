
Create a gateway {{gateway_name}} client and call the API {{resource_name}} Example of use：

```java
package demo;

import com.tencent.bkapi.{{gateway_name}}.Client;
import com.tencent.bkapi.{{gateway_name}}.RequestParams;
import okhttp3.Response;

import java.util.Map;

public class Demo {
    public static void main(String[] args) {
        try {
            Client client = new Client("https://example.apigw.com/prod/");

            // Build request parameters
            RequestParams params = new RequestParams.Builder()
                    .setData(Map.of())  // Set request parameters
                    .setPathParams(Map.of())  // Set path parameters
                    .setQueryParams(Map.of())  // Set querystring
                    .setHeaders(Map.of())  // Set request headers
                    .setTimeout(10)  // Set timeout
                    .setBkAppCode("x")  // Set application authentication
                    .setBkAppSecret("y")  // Set application authentication
                    .setBkToken("z")  // Set user authentication
                    .build();

            // Make the request
            Response response = client.{{resource_name}}(params);

            // Handle the response
            if (response.isSuccessful()) {
                System.out.println("Response: " + response.body().string());
            } else {
                System.err.println("Request failed: " + response.code());
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}

```

The above is only an example, please modify the parameters and the way they are called according to the actual use.

### 3. Note

The `endpoint` parameter when creating a gateway can be found in the specific gateway profile for the corresponding access address. If it is not set, it will automatically be probed using the following.
