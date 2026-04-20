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

// Package proxy is the package for proxy
package proxy

import (
	"context"
	"crypto/tls"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"sync"
	"time"

	"github.com/getkin/kin-openapi/openapi3"
	"github.com/gin-gonic/gin"
	"github.com/go-openapi/runtime"
	cli "github.com/go-openapi/runtime/client"
	"github.com/go-openapi/strfmt"
	"github.com/modelcontextprotocol/go-sdk/mcp"
	"github.com/spf13/cast"
	"go.uber.org/zap"

	"mcp_proxy/pkg/constant"
	"mcp_proxy/pkg/infra/logging"
	"mcp_proxy/pkg/util"
)

const (
	toolResponseStatusCodeField = "status_code"
	toolResponseRequestIDField  = "request_id"
	toolResponseBodyField       = "response_body"
)

// MCPProxy ...
type MCPProxy struct {
	mcpServers map[string]*MCPServer
	rwLock     *sync.RWMutex
	// 运行的mcp server
	activeMCPServers    map[string]struct{}
	ssePublicPathPrefix string
}

// NewMCPProxy creates a proxy with the given SSE public path prefix.
// The prefix is prepended to req.URL.Path before passing to SSEHandler so the
// endpoint event matches the client-visible URL behind a reverse proxy.
func NewMCPProxy(ssePublicPathPrefix string) *MCPProxy {
	return &MCPProxy{
		mcpServers:          map[string]*MCPServer{},
		rwLock:              &sync.RWMutex{},
		activeMCPServers:    map[string]struct{}{},
		ssePublicPathPrefix: ssePublicPathPrefix,
	}
}

// AddMCPServer ...
func (m *MCPProxy) AddMCPServer(name string, mcpServer *MCPServer) {
	m.rwLock.Lock()
	defer m.rwLock.Unlock()
	logging.GetLogger().Infof("add mcp server: %s", name)
	m.mcpServers[name] = mcpServer
}

// GetActiveMCPServerNames ...
func (m *MCPProxy) GetActiveMCPServerNames() []string {
	m.rwLock.RLock()
	defer m.rwLock.RUnlock()
	var names []string
	for name := range m.activeMCPServers {
		names = append(names, name)
	}
	return names
}

// IsMCPServerExist ...
func (m *MCPProxy) IsMCPServerExist(name string) bool {
	m.rwLock.RLock()
	defer m.rwLock.RUnlock()
	_, ok := m.mcpServers[name]
	return ok
}

// GetMCPServer ...
func (m *MCPProxy) GetMCPServer(name string) *MCPServer {
	m.rwLock.RLock()
	defer m.rwLock.RUnlock()
	return m.mcpServers[name]
}

func buildToolInputSchema(toolConfig *ToolConfig, serverName string) map[string]any {
	schemaBytes, err := toolConfig.ParamSchema.JSONSchemaBytes()
	if err != nil {
		logging.GetLogger().Error("failed to convert ParamSchema to JSON schema bytes",
			zap.Error(err),
			zap.String("tool_name", toolConfig.Name),
			zap.String("mcp_server", serverName),
		)
	}

	inputSchema := map[string]any{"type": "object", "properties": map[string]any{}}
	if len(schemaBytes) > 0 {
		if err := json.Unmarshal(schemaBytes, &inputSchema); err != nil {
			logging.GetLogger().Error("failed to unmarshal tool input schema",
				zap.Error(err),
				zap.String("tool_name", toolConfig.Name),
				zap.String("mcp_server", serverName),
			)
			inputSchema = map[string]any{"type": "object", "properties": map[string]any{}}
		}
	}
	if _, ok := inputSchema["properties"]; !ok {
		inputSchema["properties"] = map[string]any{}
	}
	return inputSchema
}

//nolint:unused // temporarily unused while OutputSchema is disabled
func hasObjectSchemaType(schemaType any) bool {
	switch value := schemaType.(type) {
	case string:
		return value == "object"
	case []string:
		for _, item := range value {
			if item == "object" {
				return true
			}
		}
	case []any:
		for _, item := range value {
			if itemStr, ok := item.(string); ok && itemStr == "object" {
				return true
			}
		}
	}
	return false
}

//nolint:unused // temporarily unused while OutputSchema is disabled
func normalizeToolOutputSchema(outputSchema map[string]any) map[string]any {
	schemaType, hasType := outputSchema["type"]
	_, hasProperties := outputSchema["properties"]
	if hasObjectSchemaType(schemaType) || (!hasType && hasProperties) {
		if !hasType {
			outputSchema["type"] = "object"
		}
		if !hasProperties {
			outputSchema["properties"] = map[string]any{}
		}
	}
	return outputSchema
}

//nolint:unused // temporarily unused while OutputSchema is disabled
func buildToolOutputSchema(toolConfig *ToolConfig, serverName string) any {
	if len(toolConfig.OutputSchema) == 0 {
		return nil
	}

	var outputSchema map[string]any
	if err := json.Unmarshal(toolConfig.OutputSchema, &outputSchema); err != nil {
		logging.GetLogger().Error("failed to unmarshal tool output schema",
			zap.Error(err),
			zap.String("tool_name", toolConfig.Name),
			zap.String("mcp_server", serverName),
		)
		return nil
	}

	// go-sdk 的 AddTool 要求 OutputSchema 顶层为 object；数组或 ref-only schema 直接忽略。
	schemaType, hasType := outputSchema["type"]
	_, hasProperties := outputSchema["properties"]
	if !hasObjectSchemaType(schemaType) && (hasType || !hasProperties) {
		return nil
	}

	return normalizeToolOutputSchema(outputSchema)
}

func buildToolResponseEnvelope(statusCode int, requestID string, responseBody any) map[string]any {
	responseResult := map[string]any{
		toolResponseStatusCodeField: statusCode,
		toolResponseRequestIDField:  requestID,
	}
	if responseBody != nil {
		responseResult[toolResponseBodyField] = responseBody
	}
	return responseResult
}

func buildToolResult(output any) *mcp.CallToolResult {
	result := &mcp.CallToolResult{}
	// FIXME: StructuredContent temporarily disabled along with OutputSchema.
	// Returning StructuredContent without a valid OutputSchema causes MCP client-side errors.
	// Re-enable after fixing OutputSchema (target: 2026-04-15, owner: @Han-Ya-Jun).
	// if structuredContent, ok := output.(map[string]any); ok {
	// 	result.StructuredContent = structuredContent
	// }
	text := cast.ToString(output)
	if rawOutput, err := json.Marshal(output); err == nil {
		text = string(rawOutput)
	}
	result.Content = []mcp.Content{
		&mcp.TextContent{Text: text},
	}
	return result
}

func buildMCPTool(toolConfig *ToolConfig, serverName string) *mcp.Tool {
	tool := &mcp.Tool{
		Name:        toolConfig.Name,
		Description: toolConfig.Description,
		InputSchema: buildToolInputSchema(toolConfig, serverName),
	}
	// FIXME: OutputSchema temporarily disabled because certain OpenAPI response schemas
	// cause MCP client-side validation failures when StructuredContent is returned.
	// Re-enable after fixing schema normalization logic (target: 2026-04-15, owner: @Han-Ya-Jun).
	// if outputSchema := buildToolOutputSchema(toolConfig, serverName); outputSchema != nil {
	// 	tool.OutputSchema = outputSchema
	// }
	return tool
}

// AddMCPServerFromConfigs ...
func (m *MCPProxy) AddMCPServerFromConfigs(configs []*MCPServerConfig) error {
	for _, config := range configs {
		var mcpServer *MCPServer

		// 创建 MCP Server
		server := mcp.NewServer(&mcp.Implementation{
			Name:    config.Name,
			Title:   config.Title,
			Version: fmt.Sprintf("%d", config.ResourceVersionID),
		}, nil)

		if config.ProtocolType == constant.MCPServerProtocolTypeStreamableHTTP {
			// 创建 Streamable HTTP Handler，启用 Stateless 模式避免 session not found 错误
			httpHandler := mcp.NewStreamableHTTPHandler(func(r *http.Request) *mcp.Server {
				return server
			}, &mcp.StreamableHTTPOptions{
				Stateless: true,
			})
			mcpServer = NewStreamableHTTPMCPServer(
				server, httpHandler, config.Name, config.ResourceVersionID, config.RawResponseEnabled,
			)
		} else {
			// 默认使用 SSE Handler
			sseHandler := mcp.NewSSEHandler(func(r *http.Request) *mcp.Server {
				return server
			}, nil)
			mcpServer = NewMCPServer(server, sseHandler, config.Name, config.ResourceVersionID, config.RawResponseEnabled)
		}

		// register tool
		for _, toolConfig := range config.Tools {
			toolHandler := genToolHandler(toolConfig, config.Name, config.RawResponseEnabled)
			mcpServer.AddTool(buildMCPTool(toolConfig, config.Name), toolHandler)
		}
		m.AddMCPServer(config.Name, mcpServer)
	}
	return nil
}

// AddMCPServerFromOpenAPISpec nolint:gofmt
// operationIDList: 需要注册的 operationID 列表（即纯资源名列表）
// toolNameMap: 资源名到工具名的映射，如果为 nil 则使用资源名作为工具名
func (m *MCPProxy) AddMCPServerFromOpenAPISpec(name string,
	resourceVersionID int, openAPISpec *openapi3.T, operationIDList []string,
	toolNameMap map[string]string, protocolType string, rawResponseEnabled bool,
) error {
	operationIDMap := make(map[string]struct{})
	for _, operationID := range operationIDList {
		operationIDMap[operationID] = struct{}{}
	}
	mcpServerConfig := &MCPServerConfig{
		Name:               name,
		Tools:              OpenapiToMcpToolConfig(openAPISpec, operationIDMap, toolNameMap),
		ResourceVersionID:  resourceVersionID,
		ProtocolType:       protocolType,
		RawResponseEnabled: rawResponseEnabled,
	}
	return m.AddMCPServerFromConfigs([]*MCPServerConfig{mcpServerConfig})
}

// UpdateMCPServerFromOpenApiSpec nolint:gofmt
// operationIDList: 需要注册的 operationID 列表（即纯资源名列表）
// toolNameMap: 资源名到工具名的映射，如果为 nil 则使用资源名作为工具名
func (m *MCPProxy) UpdateMCPServerFromOpenApiSpec(
	mcpServer *MCPServer, name string, resourceVersionID int, openAPISpec *openapi3.T,
	operationIDList []string, toolNameMap map[string]string,
) error {
	operationIDMap := make(map[string]struct{})
	for _, operationID := range operationIDList {
		operationIDMap[operationID] = struct{}{}
	}
	mcpServerConfig := &MCPServerConfig{
		Name:               name,
		Tools:              OpenapiToMcpToolConfig(openAPISpec, operationIDMap, toolNameMap),
		RawResponseEnabled: mcpServer.RawResponseEnabled(),
	}
	// update tool
	for _, toolConfig := range mcpServerConfig.Tools {
		toolHandler := genToolHandler(toolConfig, name, mcpServer.RawResponseEnabled())
		mcpServer.AddTool(buildMCPTool(toolConfig, name), toolHandler)
	}
	// 更新资源版本号
	mcpServer.SetResourceVersionID(resourceVersionID)
	return nil
}

// SseHandler ...
func (m *MCPProxy) SseHandler() gin.HandlerFunc {
	return func(c *gin.Context) {
		name := c.Param("name")
		mcpServer := m.GetMCPServer(name)
		if mcpServer == nil {
			util.BadRequestErrorJSONResponse(c, fmt.Sprintf("mcp server name %s does not exist", name))
			logging.GetLogger().Warnf("mcp server name %s does not exist", name)
			return
		}
		handler := mcpServer.HandleSSE()
		if handler == nil {
			util.BadRequestErrorJSONResponse(c, fmt.Sprintf("mcp server %s does not support SSE protocol", name))
			return
		}
		handler.ServeHTTP(c.Writer, util.RequestWithPublicPathPrefix(c.Request, m.ssePublicPathPrefix))
	}
}

// StreamableHTTPHandler Streamable HTTP 协议 Handler
func (m *MCPProxy) StreamableHTTPHandler() gin.HandlerFunc {
	return func(c *gin.Context) {
		name := c.Param("name")
		mcpServer := m.GetMCPServer(name)
		if mcpServer == nil {
			util.BadRequestErrorJSONResponse(c, fmt.Sprintf("mcp server name %s does not exist", name))
			logging.GetLogger().Warnf("mcp server name %s does not exist", name)
			return
		}
		handler := mcpServer.HandleMCP()
		if handler == nil {
			util.BadRequestErrorJSONResponse(
				c,
				fmt.Sprintf("mcp server %s does not support Streamable HTTP protocol", name),
			)
			return
		}
		handler.ServeHTTP(c.Writer, c.Request)
	}
}

// Run ...
func (m *MCPProxy) Run(ctx context.Context) {
	m.rwLock.Lock()
	defer m.rwLock.Unlock()
	for _, mcpServer := range m.mcpServers {
		if _, ok := m.activeMCPServers[mcpServer.name]; ok {
			continue
		}
		mcpServer.Run(ctx)
		m.activeMCPServers[mcpServer.name] = struct{}{}
	}
}

// DeleteMCPServer delete and shutdown mcp server
func (m *MCPProxy) DeleteMCPServer(name string) {
	m.rwLock.Lock()
	defer m.rwLock.Unlock()
	if _, ok := m.mcpServers[name]; !ok {
		return
	}
	mcpServer := m.mcpServers[name]
	mcpServer.Shutdown(context.Background())
	delete(m.mcpServers, name)
	delete(m.activeMCPServers, name)
}

// RegisterPromptsToMCPServer registers prompts to the specified MCP server
func (m *MCPProxy) RegisterPromptsToMCPServer(serverName string, prompts []*PromptConfig) {
	mcpServer := m.GetMCPServer(serverName)
	if mcpServer == nil {
		return
	}
	for _, promptConfig := range prompts {
		prompt, handler := genPromptAndHandler(promptConfig)
		mcpServer.AddPrompt(prompt, handler)
	}
}

// UpdateMCPServerPrompts updates prompts for the specified MCP server
func (m *MCPProxy) UpdateMCPServerPrompts(serverName string, prompts []*PromptConfig) {
	mcpServer := m.GetMCPServer(serverName)
	if mcpServer == nil {
		return
	}
	// 构建新的 prompt 名称集合
	newPromptNames := make(map[string]struct{})
	for _, p := range prompts {
		newPromptNames[p.Name] = struct{}{}
	}
	// 删除不再存在的 prompts
	for _, existingPrompt := range mcpServer.GetPromptNames() {
		if _, ok := newPromptNames[existingPrompt]; !ok {
			mcpServer.RemovePrompt(existingPrompt)
		}
	}
	// 注册新的 prompts
	for _, promptConfig := range prompts {
		prompt, handler := genPromptAndHandler(promptConfig)
		mcpServer.AddPrompt(prompt, handler)
	}
}

func genPromptAndHandler(promptConfig *PromptConfig) (*mcp.Prompt, PromptHandler) {
	prompt := &mcp.Prompt{
		Name:        promptConfig.Name,
		Description: promptConfig.Description,
	}
	handler := func(ctx context.Context, req *mcp.GetPromptRequest) (*mcp.GetPromptResult, error) {
		return &mcp.GetPromptResult{
			Description: promptConfig.Description,
			Messages: []*mcp.PromptMessage{
				{
					Role: mcp.Role("user"),
					Content: &mcp.TextContent{
						Text: promptConfig.Content,
					},
				},
			},
		}, nil
	}
	return prompt, handler
}

// loggingTransport 是一个带日志的 HTTP Transport
type loggingTransport struct {
	base      http.RoundTripper
	logger    *zap.SugaredLogger
	appCode   string
	username  string
	requestID string
	toolName  string
}

// RoundTrip 实现 http.RoundTripper 接口
func (t *loggingTransport) RoundTrip(req *http.Request) (*http.Response, error) {
	start := time.Now()

	// 记录请求日志
	t.logger.Infow("outgoing request",
		"app_code", t.appCode,
		"username", t.username,
		"request_id", t.requestID,
		"tool", t.toolName,
		"method", req.Method,
		"url", req.URL.String(),
		"host", req.Host,
	)

	// 执行请求
	resp, err := t.base.RoundTrip(req)

	duration := time.Since(start)

	if err != nil {
		t.logger.Errorw("outgoing request failed",
			"app_code", t.appCode,
			"username", t.username,
			"request_id", t.requestID,
			"tool", t.toolName,
			"method", req.Method,
			"url", req.URL.String(),
			"duration", duration,
			"error", err,
		)
		return nil, err
	}

	// 记录响应日志
	t.logger.Infow("outgoing response",
		"app_code", t.appCode,
		"username", t.username,
		"request_id", t.requestID,
		"tool", t.toolName,
		"method", req.Method,
		"url", req.URL.String(),
		"status_code", resp.StatusCode,
		"duration", duration,
	)

	return resp, nil
}

func genToolHandler(toolApiConfig *ToolConfig, serverName string, rawResponse bool) ToolHandler {
	// 生成handler
	handler := func(ctx context.Context, req *mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		auditLog := logging.GetAuditLoggerWithContext(ctx)
		requestID := util.GetRequestIDFromContext(ctx)
		appCode := util.GetAppCodeFromContext(ctx)
		username := util.GetUsernameFromContext(ctx)

		// 在所有日志中添加 app_code 和 username
		auditLog = auditLog.With(
			zap.String("tool", toolApiConfig.String()),
			zap.String("app_code", appCode),
			zap.String("username", username),
		)
		// 延迟签发 inner JWT - 只有在调用外部 API 时才签发
		innerJwt, err := util.SignInnerJWTFromContext(ctx)
		if err != nil {
			auditLog.Error("sign inner jwt err", zap.Error(err))
			return nil, fmt.Errorf("sign inner jwt failed: %w", err)
		}
		auditLog.Info("call tool", zap.Any("request", req.Params.Arguments))
		var handlerRequest HandlerRequest
		argsBytes, err := json.Marshal(req.Params.Arguments)
		if err != nil {
			auditLog.Error("marshal arguments err", zap.Any("arguments", req.Params.Arguments), zap.Error(err))
			return nil, err
		}
		err = json.Unmarshal(argsBytes, &handlerRequest)
		if err != nil {
			auditLog.Error("unmarshal handler request err", zap.String("request",
				string(argsBytes)), zap.Error(err))
			return nil, err
		}
		// 创建带日志的 Transport
		baseTransport := &http.Transport{
			TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
		}
		logTransport := &loggingTransport{
			base:      baseTransport,
			logger:    logging.GetLogger(),
			appCode:   appCode,
			username:  username,
			requestID: requestID,
			toolName:  toolApiConfig.String(),
		}
		client := &http.Client{Transport: logTransport}
		defer client.CloseIdleConnections()
		timeout := util.GetBkApiTimeout(ctx)
		headerInfo := map[string]string{constant.BkApiTimeoutHeaderKey: fmt.Sprintf("%v", timeout)}
		requestParam := runtime.ClientRequestWriterFunc(func(req runtime.ClientRequest, _ strfmt.Registry) error {
			// 设置timeout
			_ = req.SetTimeout(timeout)
			// 设置innerJwt
			innerJwtConfig := map[string]string{
				"inner_jwt": innerJwt,
			}
			innerJwtHeaderValue, _ := json.Marshal(innerJwtConfig)
			headerInfo[constant.BkApiAuthorizationHeaderKey] = string(innerJwtHeaderValue)
			err = req.SetHeaderParam(constant.BkApiAuthorizationHeaderKey, string(innerJwtHeaderValue))
			if err != nil {
				auditLog.Error("set header param err",
					zap.String(constant.BkApiAuthorizationHeaderKey, innerJwt), zap.Error(err))
				return err
			}
			// 设置request id
			if requestID != "" {
				headerInfo[constant.RequestIDHeaderKey] = requestID
				_ = req.SetHeaderParam(constant.RequestIDHeaderKey, requestID)
			}

			// 设置header
			headers := util.GetBkApiAllowedHeaders(ctx)
			for key, vlue := range headers {
				_ = req.SetHeaderParam(key, vlue)
				headerInfo[key] = vlue
			}
			// 如果没有单独设置 Content-Type，则默认设置为 application/json
			if _, ok := headers["Content-Type"]; !ok {
				headerInfo["Content-Type"] = "application/json"
				_ = req.SetHeaderParam("Content-Type", "application/json")
			}

			if handlerRequest.HeaderParam != nil {
				for k, v := range handlerRequest.HeaderParam {
					err = req.SetHeaderParam(k, fmt.Sprintf("%v", v))
					if err != nil {
						auditLog.Error("set header param err", zap.String(k,
							fmt.Sprintf("%v", v)), zap.Error(err))
						return err
					}
					headerInfo[k] = fmt.Sprintf("%v", v)
				}
			}
			if handlerRequest.QueryParam != nil {
				for k, v := range handlerRequest.QueryParam {
					err = req.SetQueryParam(k, fmt.Sprintf("%v", v)) // 使用 SetQueryParam 方法设置查询参数
					if err != nil {
						auditLog.Error("set query param err", zap.String(k, fmt.Sprintf("%v", v)),
							zap.Error(err))
						return err
					}
				}
			}

			if handlerRequest.PathParam != nil {
				for k, v := range handlerRequest.PathParam {
					err = req.SetPathParam(k, fmt.Sprintf("%v", v))
					if err != nil {
						auditLog.Error("set path param err",
							zap.String(k, fmt.Sprintf("%v", v)), zap.Error(err))
						return err
					}
				}
			}
			if handlerRequest.BodyParam != nil {
				err = req.SetBodyParam(handlerRequest.BodyParam)
				if err != nil {
					auditLog.Error("set body param err",
						zap.Any("body", handlerRequest.BodyParam), zap.Error(err))
					return err
				}
			}
			return nil
		})
		operation := &runtime.ClientOperation{
			ID:          toolApiConfig.Name,
			Method:      toolApiConfig.Method,
			PathPattern: toolApiConfig.Url,
			Params:      requestParam,
			Client:      client,
			Reader: runtime.ClientResponseReaderFunc(
				func(response runtime.ClientResponse, consumer runtime.Consumer) (any, error) {
					if response.Body() != nil {
						defer response.Body().Close()
					}

					var res any
					if response.Body() != nil {
						contentType := strings.ToLower(response.GetHeader("Content-Type"))
						// 根据 Content-Type 决定如何解析响应体
						if strings.Contains(contentType, "application/json") {
							// JSON 响应：使用 consumer 解析
							if e := consumer.Consume(response.Body(), &res); e != nil {
								return nil, e
							}
						} else {
							// 非 JSON 响应（text/plain, text/html 等）：读取为字符串
							bodyBytes, e := io.ReadAll(response.Body())
							if e != nil {
								return nil, e
							}
							res = string(bodyBytes)
						}
					}

					var responseResult any
					if rawResponse {
						// raw_response 模式：直接返回 API 响应结果，不添加 request_id 等额外信息
						responseResult = res
					} else {
						responseResult = buildToolResponseEnvelope(
							response.Code(),
							response.GetHeader(constant.BkGatewayRequestIDKey),
							res,
						)
					}
					if response.Code() < 200 || response.Code() > 299 {
						return nil, runtime.NewAPIError("call tool err", responseResult, response.Code())
					}
					return responseResult, nil
				},
			),
		}
		openAPIClient := cli.New(toolApiConfig.Host, toolApiConfig.BasePath, []string{toolApiConfig.Schema})
		submit, err := openAPIClient.Submit(operation)
		if err != nil {
			msg := fmt.Sprintf("call %s error:%s", toolApiConfig, err.Error())
			auditLog.Error("call tool err", zap.Any("header", headerInfo), zap.Error(err))
			// nolint:nilerr
			return &mcp.CallToolResult{
				Content: []mcp.Content{
					&mcp.TextContent{
						Text: msg,
					},
				},
				IsError: true,
			}, nil
		}
		auditLog.Info("call tool success", zap.String("tool", toolApiConfig.String()),
			zap.Any("response", submit), zap.Any("header", headerInfo))
		return buildToolResult(submit), nil
	}
	return handler
}
