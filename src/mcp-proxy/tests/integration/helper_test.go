/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */

package integration_test

import (
	"bufio"
	"bytes"
	"context"
	"crypto/rsa"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"

	jwt "github.com/golang-jwt/jwt/v4"

	"mcp_proxy/pkg/constant"
	"mcp_proxy/pkg/util"
)

// 测试配置，可通过环境变量覆盖
var (
	mcpProxyBaseURL = getEnv("MCP_PROXY_URL", "http://127.0.0.1:8889")
)

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// TestClient 测试客户端
type TestClient struct {
	BaseURL    string
	HTTPClient *http.Client
	PrivateKey *rsa.PrivateKey
}

// MCPRequest MCP 请求结构
type MCPRequest struct {
	JSONRPC string      `json:"jsonrpc"`
	ID      interface{} `json:"id"`
	Method  string      `json:"method"`
	Params  interface{} `json:"params,omitempty"`
}

// MCPResponse MCP 响应结构
type MCPResponse struct {
	JSONRPC string          `json:"jsonrpc"`
	ID      interface{}     `json:"id"`
	Result  json.RawMessage `json:"result,omitempty"`
	Error   *MCPError       `json:"error,omitempty"`
}

// MCPError MCP 错误结构
type MCPError struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
}

// ToolsListResult tools/list 响应结果
type ToolsListResult struct {
	Tools []ToolInfo `json:"tools"`
}

// ToolInfo 工具信息
type ToolInfo struct {
	Name        string          `json:"name"`
	Description string          `json:"description,omitempty"`
	InputSchema json.RawMessage `json:"inputSchema,omitempty"`
}

// PromptsListResult prompts/list 响应结果
type PromptsListResult struct {
	Prompts []PromptInfo `json:"prompts"`
}

// PromptInfo Prompt 信息
type PromptInfo struct {
	Name        string `json:"name"`
	Description string `json:"description,omitempty"`
}

// InitializeResult initialize 响应结果
type InitializeResult struct {
	ProtocolVersion string                 `json:"protocolVersion"`
	ServerInfo      map[string]interface{} `json:"serverInfo"`
	Capabilities    map[string]interface{} `json:"capabilities"`
}

// CustomClaims JWT claims
type CustomClaims struct {
	App  AppInfo  `json:"app"`
	User UserInfo `json:"user"`
	jwt.RegisteredClaims
}

// AppInfo 应用信息
type AppInfo struct {
	AppCode  string `json:"app_code"`
	Verified bool   `json:"verified"`
}

// UserInfo 用户信息
type UserInfo struct {
	Username string `json:"username"`
	Verified bool   `json:"verified"`
}

// 测试用的加密私钥配置 (与 init.sql 和 docker-compose.yml 中的配置匹配)
const (
	testEncryptKey          = "OWtSMTM0MG4zVDA1dnNpRGpGa1B6SnExYzFjQ2ZXMTM="
	testCryptoNonce         = "q76rE8srRuYM"
	testEncryptedPrivateKey = "fb635e8543dde12366bfa92ef24fbf82957b0610faabeb4ad5e55e1168177f30340739a37e757f671519df5cdf222f2d3362d5db50c9c26fc77c611389fe595aa00aea35dff9f074bb832bc80fcc92588d2c7987333081afea49f556106545733ad8e0076205dfa5dfb295b8e8cbff8d5c9fe3613cc06a9b46f7a20040304b8172c8bf632ea7323b0e249cae066d969e5c2d804325f6be787973f983f4b6dfbfa7dafb0ee70d1f2d62fd1621e6ec828c6386945b8a4106739368db32be0b0cfbe8f4b041e2410ddfd5f35025774b072b12393a4fd8495dbfb3dacc815d1ae1669b410e8610a8e365c7237079aeac94514a9cf77114c6d52349ff58696c7b3c35830b8f9b281532d74bf203e973fbe3791446006a7690e1fbab411c375a977298e4d5bda0d256ad8377a32ad637b256d0727a8862ea733c2cfe9b71ef17d85950efca942a47d98ca45ba030ed79ad6239042000f4806f1b5b82dea74efe66758584000af6291f02cec2a5d3c6e9d0d544c8dedd07a75f09268cf3e55c8d9e1cc21100de4612959ce8052fb3b6b42ba295ac956ca091f804d18cd8e333c3192dbb65f6654afaa7d280185ce596dafb2b08a0d3b2d92c035fce00c6e39bb49da71e7bd0116fa81453c497e5b17e511fd439db2511fddfe105eaa0ca6628d384cad886d69f0be8aedba48b4e550b3b206c55002ab17713086717cb9da98ba13698a24b6043a4451ec7fae070435f600184528ac3049a73c8da7a15856b7f6117859636ea97d58cdf8fefe2197cbe1de917325670b71dc2fccaa58ed220676a89f90342fb6579cde472440108c45c6b058652e7dfd895ccf651820bf41a2eb7c418abb816171868d15a7df1fa829d02d810fc5dfce4edd23792430aafa993ccc412e6a5acf412db47976fd00e9f19935e23472fe6f0f7c06a598947a5b572ead217c71b9cad74c6d965720e419e5ea771905e2bf7b7e3cd517bc3138c10755797ad1c2ed29904aef76b3c8cb773f2fa1be288685ab01171a3196459810bd9a4153def1a00dc914620b2cfdcf2d3a134e93b415aae2e733e7dff9b3fc95cd111cee41617b08798983b9b7e399d4a03e836230e7bb8d4b107dd8d3f75737daa9fac94fca20345d04d9043ad737b1c96d39f2b26937406a61c50b470c5a48973be7da9b5a59a2b4f444a91a0e76cdfaccf2902a792824664dcff12234b2e0cd4d05586eadc2d6b0f7c6e9d5f757a90fec55d1b689ee85bdfd03f900ae577953383cab48b357f21fd342a6109cc4202a21b1dffa20269886f23e22d2c4bce26cfb2a2c8ca251f86324a719d664b1a9b13d9e2ec88ee52d6668f80ec88378d5d3c5bdf48fcab5de1202f7b259da30e41efc054241d5e325a2306175db20674a2b98fbfd6a430462196fa950fbcb062ea9fd55f5b87677c2be5ba0d277adfc027b95d4efc9c22c9a660085d01585b1ddb6c2b071d730b69d55c010005e47b897ef6fe57051bb28031f702c3258959b4eb2fbd08b0c4c66a6088d14448c78ca0f7657c3012c8b4b209e605528dc9855ec183cff45f35d7ff6575ae784cadac34ad3f440391fdf945fbb305deffb64507c4d073bf0e07c0f6047d5bd98eb751550d62f75dcb791406b24a0b37ed84a12a27f6118d82f936f91aa59196ad39a0b34cc18079312bd89083065d9ea97abee142fc969a237c508f32b82a169779621f2527a7facdac8a091cc95e451b403b1b0fa55c0233e424a089c606bad159d01a31c9168aceadaae6736d4c98d43890137bac56632fcad19300dd2d70ba528a6645f62471001acb38be5b066c964ad38d960e248a773c87f0132f896241cd9e1ddb62b99a9387029022acf4d63b3210cab6f7aa5fb73d0e5fa3b9fecaeb288dd777fa279a3af87b8026c77a6bad455ab6697966464dc2acea73e25fbac3492c990734ba22d370ce8db71a44ff6e8dd341e6fe4b5ca04110c67d3456eeff1e5f20a08b0e4ffae08a452e6664486c7536aebce1a18af966ac0d9cd80d372ce2001b10e40f4d79614138f258ddb109fcd62a5e37481503b7e746efd1278f31a43bdc694cc6efac78bfc4448b5e370baabc38d6da1f139a713ca47d4b872d5c418de926884866285d619ae4863f78cf673dffca4224b10d6a12fb18d2871daffb8f5fed67c9df62bde5806f7961ea928bad3889f17cf329038a9eecc9813fb61cd77e8c5fb3229514e7b6c55d4c14da58e37df81b23a6cc6aedc650c882719ef0116adf1c385c6774e6f0c8eb502dd125e875316f17af6c3c1c510c2c0b8d680c054362064b8c15e941761751a076bc3dfaa20755c437573a4fab2b297c426acc91dea9bd3fd6a0d38ea3377c2276131f5a891adc777a8097e66b9af9e8c7c037a2046821decf"
)

// NewTestClient 创建测试客户端
func NewTestClient() (*TestClient, error) {
	// 使用 AESGCMDecrypt 解密私钥
	privateKeyPEM, err := util.AESGCMDecrypt(testEncryptKey, testCryptoNonce, testEncryptedPrivateKey)
	if err != nil {
		return nil, fmt.Errorf("failed to decrypt private key: %w", err)
	}

	// 解析私钥
	key, err := util.ParsePrivateKey([]byte(privateKeyPEM))
	if err != nil {
		return nil, fmt.Errorf("failed to parse private key: %w", err)
	}

	privateKey, ok := key.(*rsa.PrivateKey)
	if !ok {
		return nil, fmt.Errorf("private key is not RSA type")
	}

	return &TestClient{
		BaseURL: mcpProxyBaseURL,
		HTTPClient: &http.Client{
			Timeout: 30 * time.Second,
		},
		PrivateKey: privateKey,
	}, nil
}

// GenerateJWT 生成测试用 JWT token
func (c *TestClient) GenerateJWT(appCode, username string) (string, error) {
	// 使用稍早的时间来避免本地和 Docker 容器之间的时间差异导致 iat 验证失败
	now := time.Now().Add(-time.Minute)
	claims := &CustomClaims{
		App: AppInfo{
			AppCode:  appCode,
			Verified: true,
		},
		User: UserInfo{
			Username: username,
			Verified: true,
		},
		RegisteredClaims: jwt.RegisteredClaims{
			Issuer:    "test-issuer",
			Audience:  jwt.ClaimStrings{"test-audience"},
			ExpiresAt: jwt.NewNumericDate(now.Add(time.Hour)),
			IssuedAt:  jwt.NewNumericDate(now),
			NotBefore: jwt.NewNumericDate(now),
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodRS512, claims)
	return token.SignedString(c.PrivateKey)
}

// DoStreamableHTTPRequest 发送 Streamable HTTP 请求
func (c *TestClient) DoStreamableHTTPRequest(
	ctx context.Context,
	serverName string,
	req *MCPRequest,
	jwtToken string,
) (*MCPResponse, error) {
	reqBody, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("marshal request failed: %w", err)
	}

	url := fmt.Sprintf("%s/%s/mcp", c.BaseURL, serverName)
	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(reqBody))
	if err != nil {
		return nil, fmt.Errorf("create request failed: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Accept", "application/json, text/event-stream")
	if jwtToken != "" {
		httpReq.Header.Set(constant.BkGatewayJWTHeaderKey, jwtToken)
	}

	resp, err := c.HTTPClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("do request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("unexpected status code: %d, body: %s", resp.StatusCode, string(body))
	}

	// 检查响应类型
	contentType := resp.Header.Get("Content-Type")
	if strings.Contains(contentType, "text/event-stream") {
		// SSE 响应，解析 SSE 事件
		return c.parseSSEResponse(resp.Body)
	}

	// JSON 响应
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("read response body failed: %w", err)
	}

	var mcpResp MCPResponse
	if err := json.Unmarshal(body, &mcpResp); err != nil {
		return nil, fmt.Errorf("unmarshal response failed: %w, body: %s", err, string(body))
	}

	return &mcpResp, nil
}

// parseSSEResponse 解析 SSE 响应
func (c *TestClient) parseSSEResponse(body io.Reader) (*MCPResponse, error) {
	scanner := bufio.NewScanner(body)
	var dataLines []string

	for scanner.Scan() {
		line := scanner.Text()
		if strings.HasPrefix(line, "data: ") {
			data := strings.TrimPrefix(line, "data: ")
			dataLines = append(dataLines, data)
		}
	}

	if len(dataLines) == 0 {
		return nil, fmt.Errorf("no data in SSE response")
	}

	// 取最后一个 data 行（通常是完整的响应）
	lastData := dataLines[len(dataLines)-1]
	var mcpResp MCPResponse
	if err := json.Unmarshal([]byte(lastData), &mcpResp); err != nil {
		return nil, fmt.Errorf("unmarshal SSE data failed: %w, data: %s", err, lastData)
	}

	return &mcpResp, nil
}

// HealthCheck 检查 mcp-proxy 服务是否可用
func (c *TestClient) HealthCheck(ctx context.Context) error {
	url := fmt.Sprintf("%s/ping", c.BaseURL)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return err
	}

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("health check failed: status %d", resp.StatusCode)
	}

	return nil
}

// WaitForService 等待服务可用
func (c *TestClient) WaitForService(ctx context.Context, timeout time.Duration) error {
	deadline := time.Now().Add(timeout)
	for time.Now().Before(deadline) {
		if err := c.HealthCheck(ctx); err == nil {
			return nil
		}
		time.Sleep(time.Second)
	}
	return fmt.Errorf("service not available after %v", timeout)
}
