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
	"net/http"
	"sync"
	"time"

	"github.com/getkin/kin-openapi/openapi3"
	"github.com/gin-gonic/gin"
	"github.com/go-openapi/runtime"
	cli "github.com/go-openapi/runtime/client"
	"github.com/go-openapi/strfmt"
	"github.com/modelcontextprotocol/go-sdk/mcp"
	"github.com/spf13/cast"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/codes"
	semconv "go.opentelemetry.io/otel/semconv/v1.10.0"
	oteltrace "go.opentelemetry.io/otel/trace"
	"go.uber.org/zap"

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/constant"
	"mcp_proxy/pkg/infra/logging"
	"mcp_proxy/pkg/infra/trace"
	"mcp_proxy/pkg/util"
)

// MCPProxy ...
type MCPProxy struct {
	mcpServers map[string]*MCPServer
	rwLock     *sync.RWMutex
	// 运行的mcp server
	activeMCPServers map[string]struct{}
}

// NewMCPProxy ...
func NewMCPProxy() *MCPProxy {
	return &MCPProxy{
		mcpServers:       map[string]*MCPServer{},
		rwLock:           &sync.RWMutex{},
		activeMCPServers: map[string]struct{}{},
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

// AddMCPServerFromConfigs ...
func (m *MCPProxy) AddMCPServerFromConfigs(configs []*MCPServerConfig) error {
	for _, config := range configs {
		var mcpServer *MCPServer

		// 创建 MCP Server
		server := mcp.NewServer(&mcp.Implementation{Name: config.Name}, nil)

		if config.ProtocolType == constant.MCPServerProtocolTypeStreamableHTTP {
			// 创建 Streamable HTTP Handler
			httpHandler := mcp.NewStreamableHTTPHandler(func(r *http.Request) *mcp.Server {
				return server
			}, nil)
			mcpServer = NewStreamableHTTPMCPServer(server, httpHandler, config.Name, config.ResourceVersionID)
		} else {
			// 默认使用 SSE Handler
			sseHandler := mcp.NewSSEHandler(func(r *http.Request) *mcp.Server {
				return server
			}, nil)
			mcpServer = NewMCPServer(server, sseHandler, config.Name, config.ResourceVersionID)
		}

		// register tool
		for _, toolConfig := range config.Tools {
			schemaBytes, err := toolConfig.ParamSchema.JSONSchemaBytes()
			if err != nil {
				logging.GetLogger().Error("failed to convert ParamSchema to JSON schema bytes",
					zap.Error(err),
					zap.String("tool_name", toolConfig.Name),
					zap.String("mcp_server", config.Name),
				)
			}
			// 默认提供空对象 schema，避免 AddTool panic
			inputSchema := map[string]any{"type": "object"}
			if len(schemaBytes) > 0 {
				if err := json.Unmarshal(schemaBytes, &inputSchema); err != nil {
					logging.GetLogger().Error("failed to unmarshal tool input schema",
						zap.Error(err),
						zap.String("tool_name", toolConfig.Name),
						zap.String("mcp_server", config.Name),
					)
					// 保持默认的空对象 schema
					inputSchema = map[string]any{"type": "object"}
				}
			}
			tool := &mcp.Tool{
				Name:        toolConfig.Name,
				Description: toolConfig.Description,
				InputSchema: inputSchema,
			}
			// 处理 OutputSchema
			if len(toolConfig.OutputSchema) > 0 {
				var outputSchema map[string]any
				if err := json.Unmarshal(toolConfig.OutputSchema, &outputSchema); err != nil {
					logging.GetLogger().Error("failed to unmarshal tool output schema",
						zap.Error(err),
						zap.String("tool_name", toolConfig.Name),
						zap.String("mcp_server", config.Name),
					)
				} else {
					// 确保 OutputSchema 包含 type: "object"，否则 SDK 会 panic
					if _, ok := outputSchema["type"]; !ok {
						outputSchema["type"] = "object"
					}
					tool.OutputSchema = outputSchema
				}
			}
			toolHandler := genToolHandler(toolConfig)
			mcpServer.AddTool(tool, toolHandler)
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
	toolNameMap map[string]string, protocolType string,
) error {
	operationIDMap := make(map[string]struct{})
	for _, operationID := range operationIDList {
		operationIDMap[operationID] = struct{}{}
	}
	mcpServerConfig := &MCPServerConfig{
		Name:              name,
		Tools:             OpenapiToMcpToolConfig(openAPISpec, operationIDMap, toolNameMap),
		ResourceVersionID: resourceVersionID,
		ProtocolType:      protocolType,
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
		Name:  name,
		Tools: OpenapiToMcpToolConfig(openAPISpec, operationIDMap, toolNameMap),
	}
	// update tool
	for _, toolConfig := range mcpServerConfig.Tools {
		schemaBytes, err := toolConfig.ParamSchema.JSONSchemaBytes()
		if err != nil {
			logging.GetLogger().Error("failed to convert ParamSchema to JSON schema bytes",
				zap.Error(err),
				zap.String("tool_name", toolConfig.Name),
				zap.String("mcp_server", name),
			)
		}
		// 默认提供空对象 schema，避免 AddTool panic
		inputSchema := map[string]any{"type": "object"}
		if len(schemaBytes) > 0 {
			if err := json.Unmarshal(schemaBytes, &inputSchema); err != nil {
				logging.GetLogger().Error("failed to unmarshal tool input schema",
					zap.Error(err),
					zap.String("tool_name", toolConfig.Name),
					zap.String("mcp_server", name),
				)
				// 保持默认的空对象 schema
				inputSchema = map[string]any{"type": "object"}
			}
		}
		tool := &mcp.Tool{
			Name:        toolConfig.Name,
			Description: toolConfig.Description,
			InputSchema: inputSchema,
		}
		toolHandler := genToolHandler(toolConfig)
		mcpServer.AddTool(tool, toolHandler)
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
		handler.ServeHTTP(c.Writer, c.Request)
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
	base       http.RoundTripper
	logger     *zap.SugaredLogger
	appCode    string
	username   string
	requestID  string
	xRequestID string
	toolName   string
}

// RoundTrip 实现 http.RoundTripper 接口
func (t *loggingTransport) RoundTrip(req *http.Request) (*http.Response, error) {
	start := time.Now()

	// Start a trace span for the outgoing HTTP request (only when MCP tracing is enabled)
	ctx := req.Context()
	var span oteltrace.Span
	if config.G != nil && config.G.Tracing.McpAPIEnabled() {
		ctx, span = trace.StartTrace(ctx, "mcp.upstream_http")
	}
	if span != nil {
		defer span.End()
		span.SetAttributes(
			semconv.HTTPMethodKey.String(req.Method),
			semconv.HTTPURLKey.String(req.URL.String()),
			semconv.HTTPHostKey.String(req.Host),
			attribute.String("mcp.tool_name", t.toolName),
		)
		req = req.WithContext(ctx)
	}

	// 记录请求日志
	t.logger.Infow("outgoing request",
		"app_code", t.appCode,
		"username", t.username,
		"request_id", t.requestID,
		"x_request_id", t.xRequestID,
		"tool", t.toolName,
		"method", req.Method,
		"url", req.URL.String(),
		"host", req.Host,
	)

	// 执行请求
	resp, err := t.base.RoundTrip(req)

	duration := time.Since(start)

	if err != nil {
		if span != nil {
			span.SetStatus(codes.Error, err.Error())
			span.RecordError(err)
		}
		t.logger.Errorw("outgoing request failed",
			"app_code", t.appCode,
			"username", t.username,
			"request_id", t.requestID,
			"x_request_id", t.xRequestID,
			"tool", t.toolName,
			"method", req.Method,
			"url", req.URL.String(),
			"duration", duration,
			"error", err,
		)
		return nil, err
	}

	if span != nil {
		span.SetAttributes(semconv.HTTPStatusCodeKey.Int(resp.StatusCode))
		if resp.StatusCode >= 400 {
			span.SetStatus(codes.Error, fmt.Sprintf("HTTP %d", resp.StatusCode))
		}
	}

	// 记录响应日志
	t.logger.Infow("outgoing response",
		"app_code", t.appCode,
		"username", t.username,
		"request_id", t.requestID,
		"x_request_id", t.xRequestID,
		"tool", t.toolName,
		"method", req.Method,
		"url", req.URL.String(),
		"status_code", resp.StatusCode,
		"duration", duration,
	)

	return resp, nil
}

// setHandlerRequestParams sets header, query, path and body parameters from HandlerRequest onto the ClientRequest.
func setHandlerRequestParams(
	req runtime.ClientRequest,
	handlerRequest *HandlerRequest,
	headerInfo map[string]string,
	auditLog *zap.Logger,
) error {
	if handlerRequest.HeaderParam != nil {
		for k, v := range handlerRequest.HeaderParam {
			val := fmt.Sprintf("%v", v)
			if err := req.SetHeaderParam(k, val); err != nil {
				auditLog.Error("set header param err", zap.String(k, val), zap.Error(err))
				return err
			}
			headerInfo[k] = val
		}
	}
	if handlerRequest.QueryParam != nil {
		for k, v := range handlerRequest.QueryParam {
			val := fmt.Sprintf("%v", v)
			if err := req.SetQueryParam(k, val); err != nil {
				auditLog.Error("set query param err", zap.String(k, val), zap.Error(err))
				return err
			}
		}
	}
	if handlerRequest.PathParam != nil {
		for k, v := range handlerRequest.PathParam {
			val := fmt.Sprintf("%v", v)
			if err := req.SetPathParam(k, val); err != nil {
				auditLog.Error("set path param err", zap.String(k, val), zap.Error(err))
				return err
			}
		}
	}
	if handlerRequest.BodyParam != nil {
		if err := req.SetBodyParam(handlerRequest.BodyParam); err != nil {
			auditLog.Error("set body param err", zap.Any("body", handlerRequest.BodyParam), zap.Error(err))
			return err
		}
	}
	return nil
}

func genToolHandler(toolApiConfig *ToolConfig) ToolHandler {
	// 生成handler
	handler := func(ctx context.Context, req *mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		// Start a trace span for the actual upstream tool invocation (only when MCP tracing is enabled).
		// NOTE: This is intentionally separate from TracingMiddleware's "mcp.tools/call" span:
		//   - TracingMiddleware spans cover the MCP protocol layer (request/response lifecycle).
		//   - This span covers the actual upstream HTTP call to the backend API, providing
		//     tool-specific attributes (method, url, host) for fine-grained observability.
		var span oteltrace.Span
		if config.G != nil && config.G.Tracing.McpAPIEnabled() {
			ctx, span = trace.StartTrace(ctx, fmt.Sprintf("mcp.tool.%s", toolApiConfig.Name))
		}
		if span != nil {
			defer span.End()
			span.SetAttributes(
				attribute.String("mcp.tool_name", toolApiConfig.Name),
				attribute.String("mcp.tool_method", toolApiConfig.Method),
				attribute.String("mcp.tool_url", toolApiConfig.Url),
				attribute.String("mcp.tool_host", toolApiConfig.Host),
			)
		}

		auditLog := logging.GetAuditLoggerWithContext(ctx)
		requestID := util.GetRequestIDFromContext(ctx)
		xRequestID := util.GetXRequestIDFromContext(ctx)
		appCode := util.GetAppCodeFromContext(ctx)
		username := util.GetUsernameFromContext(ctx)

		// 在所有日志中添加 app_code 和 username
		auditLog = auditLog.With(
			zap.String("tool", toolApiConfig.String()),
			zap.String("app_code", appCode),
			zap.String("username", username),
		)
		// 仅在 trace_id 非空时附加，避免日志中出现空 trace_id 字段
		if traceID := trace.GetTraceIDFromContext(ctx); traceID != "" {
			auditLog = auditLog.With(zap.String("trace_id", traceID))
		}
		// 延迟签发 inner JWT - 只有在调用外部 API 时才签发
		innerJwt, err := util.SignInnerJWTFromContext(ctx)
		if err != nil {
			auditLog.Error("sign inner jwt err", zap.Error(err))
			return nil, trace.WrapErrorWithTraceID(ctx, fmt.Errorf("sign inner jwt failed: %w", err))
		}
		auditLog.Info("call tool", zap.Any("request", req.Params.Arguments))
		var handlerRequest HandlerRequest
		argsBytes, err := json.Marshal(req.Params.Arguments)
		if err != nil {
			auditLog.Error("marshal arguments err", zap.Any("arguments", req.Params.Arguments), zap.Error(err))
			return nil, trace.WrapErrorWithTraceID(ctx, err)
		}
		err = json.Unmarshal(argsBytes, &handlerRequest)
		if err != nil {
			auditLog.Error("unmarshal handler request err", zap.String("request",
				string(argsBytes)), zap.Error(err))
			return nil, trace.WrapErrorWithTraceID(ctx, err)
		}
		// 创建带日志的 Transport
		baseTransport := &http.Transport{
			TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
		}
		logTransport := &loggingTransport{
			base:       baseTransport,
			logger:     logging.GetLogger(),
			appCode:    appCode,
			username:   username,
			requestID:  requestID,
			xRequestID: xRequestID,
			toolName:   toolApiConfig.String(),
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
				headerInfo[constant.BkGatewayRequestIDKey] = requestID
				_ = req.SetHeaderParam(constant.BkGatewayRequestIDKey, requestID)
			}
			// 透传全链路 X-Request-Id
			if xRequestID != "" {
				headerInfo[constant.RequestIDHeaderKey] = xRequestID
				_ = req.SetHeaderParam(constant.RequestIDHeaderKey, xRequestID)
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

			if err = setHandlerRequestParams(req, &handlerRequest, headerInfo, auditLog); err != nil {
				return err
			}
			return nil
		})
		operation := &runtime.ClientOperation{
			ID:          toolApiConfig.Name,
			Method:      toolApiConfig.Method,
			PathPattern: toolApiConfig.Url,
			Params:      requestParam,
			Client:      client,
			Context:     ctx,
			Reader: runtime.ClientResponseReaderFunc(
				func(response runtime.ClientResponse, consumer runtime.Consumer) (any, error) {
					if response.Body() != nil {
						defer response.Body().Close()
					}
					responseResult := map[string]any{
						"status_code": response.Code(),
						"request_id":  response.GetHeader(constant.BkGatewayRequestIDKey),
					}
					var res map[string]any
					if e := consumer.Consume(response.Body(), &res); e == nil {
						responseResult["response_body"] = res
					}
					if response.Code() < 200 || response.Code() > 299 {
						return nil, runtime.NewAPIError("call tool err", responseResult, response.Code())
					}
					rawResult, _ := json.Marshal(responseResult)
					return string(rawResult), nil
				},
			),
		}
		openAPIClient := cli.New(toolApiConfig.Host, toolApiConfig.BasePath, []string{toolApiConfig.Schema})
		submit, err := openAPIClient.Submit(operation)
		if err != nil {
			msg := fmt.Sprintf("call %s error:%s", toolApiConfig, err.Error())
			auditLog.Error("call tool err", zap.Any("header", headerInfo), zap.Error(err))
			if span != nil {
				span.SetStatus(codes.Error, msg)
				span.RecordError(err)
			}
			// Append trace_id to the error message for traceability
			if traceID := trace.GetTraceIDFromContext(ctx); traceID != "" {
				msg = fmt.Sprintf("%s (trace_id=%s)", msg, traceID)
			}
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
		return &mcp.CallToolResult{
			Content: []mcp.Content{
				&mcp.TextContent{
					Text: cast.ToString(submit),
				},
			},
		}, nil
	}
	return handler
}
