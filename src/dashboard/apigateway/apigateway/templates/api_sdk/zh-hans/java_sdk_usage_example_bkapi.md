{% load json_filters %}
创建网关 {{gateway_name}} Client 并调用 API 资源 {{resource_name}} 使用示例：

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
                    .setData(Map.of())  // 设置请求参数
                    .setPathParams(Map.of())  // 设置路径参数
                    .setQueryParams(Map.of())  // 设置 querystring
                    .setHeaders(Map.of())  // 设置请求头
                    .setTimeout(10)  // 设置超时
                    .setBkAppCode("x")  // 设置应用认证
                    .setBkAppSecret("y")  // 设置应用认证
                    .setBkToken("z")  // 设置用户认证
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

以上仅为示例，具体参数及调用方式请按实际用途修改。

### 3. 注意事项

创建网关时的 `endpoint` 参数可在具体的网关简介中找到对应的访问地址。
