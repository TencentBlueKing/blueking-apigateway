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
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/codes"
	"go.opentelemetry.io/otel/propagation"
	semconv "go.opentelemetry.io/otel/semconv/v1.10.0"
	oteltrace "go.opentelemetry.io/otel/trace"
	"go.uber.org/zap"

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/constant"
	"mcp_proxy/pkg/infra/logging"
	"mcp_proxy/pkg/infra/trace"
	"mcp_proxy/pkg/util"
)

const (
	toolResponseStatusCodeField = "status_code"
	toolResponseRequestIDField  = "request_id"
	toolResponseTraceIDField    = "trace_id"
	toolResponseBodyField       = "response_body"

	// 审计日志截断阈值
	auditLogMaxBodySize     = 4096
	auditLogMaxResponseSize = 4096
)

// sensitiveHeaderKeys lists header keys whose values must be masked in logs.
var sensitiveHeaderKeys = map[string]struct{}{
	constant.BkApiAuthorizationHeaderKey: {},
	constant.BkGatewayJWTHeaderKey:       {},
}

// sharedTransport 是所有 tool call 共用的 HTTP Transport，避免每次调用创建新连接池。
// 通过 InitSharedTransport 从配置初始化，参数可在 config.yaml 的 mcpServer.transport 段调整。
var sharedTransport *http.Transport

// InitSharedTransport initializes the shared HTTP Transport from config.
// It MUST be called once during startup (before any tool calls).
// nolint:gosec
func InitSharedTransport(cfg config.Transport) {
	sharedTransport = &http.Transport{
		// NOTE: InsecureSkipVerify 跳过 TLS 证书验证，仅在内部网络环境下使用。
		// 公网环境请在 config.yaml 中设置 mcpServer.transport.insecureSkipVerify: false。
		TLSClientConfig:     &tls.Config{InsecureSkipVerify: cfg.InsecureSkipVerify},
		MaxIdleConns:        cfg.MaxIdleConns,
		MaxIdleConnsPerHost: cfg.MaxIdleConnsPerHost,
		IdleConnTimeout:     time.Duration(cfg.IdleConnTimeoutSecond) * time.Second,
	}
}

// truncateJSON 将任意对象序列化为 JSON 并截断到指定长度
func truncateJSON(v any, maxLen int) string {
	if v == nil {
		return ""
	}
	b, err := json.Marshal(v)
	if err != nil {
		return fmt.Sprintf("<marshal error: %v>", err)
	}
	s := string(b)
	if len(s) > maxLen {
		return s[:maxLen] + "...(truncated)"
	}
	return s
}

// maskSensitiveHeaders returns a copy of headerInfo with sensitive values masked.
func maskSensitiveHeaders(headerInfo map[string]string) map[string]string {
	masked := make(map[string]string, len(headerInfo))
	for k, v := range headerInfo {
		if _, ok := sensitiveHeaderKeys[k]; ok {
			if len(v) > 6 {
				masked[k] = v[:3] + "***" + v[len(v)-3:]
			} else {
				masked[k] = "***"
			}
		} else {
			masked[k] = v
		}
	}
	return masked
}

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

func buildToolOutputSchema(toolConfig *ToolConfig, serverName string) any {
	if len(toolConfig.OutputSchema) == 0 {
		return nil
	}

	// go-sdk 的低层 AddTool 要求 OutputSchema 顶层是 object，且 handler 返回的 structuredContent 也必须是 object。
	// 当前 proxy 统一返回带元信息的 response envelope，因此这里期望 OutputSchema 已经是该 envelope 对象。
	var outputSchema map[string]any
	if err := json.Unmarshal(toolConfig.OutputSchema, &outputSchema); err != nil {
		logging.GetLogger().Error("failed to unmarshal tool output schema",
			zap.Error(err),
			zap.String("tool_name", toolConfig.Name),
			zap.String("mcp_server", serverName),
		)
		return nil
	}
	outputSchema = normalizeToolOutputSchema(outputSchema)
	if !hasObjectSchemaType(outputSchema["type"]) {
		logging.GetLogger().Warn("skip unsupported tool output schema",
			zap.String("tool_name", toolConfig.Name),
			zap.String("mcp_server", serverName),
			zap.Any("output_schema_type", outputSchema["type"]),
		)
		return nil
	}
	return outputSchema
}

func buildToolResponseEnvelope(statusCode int, requestID, traceID string, responseBody any) map[string]any {
	responseResult := map[string]any{
		toolResponseStatusCodeField: statusCode,
		toolResponseRequestIDField:  requestID,
		toolResponseTraceIDField:    traceID,
	}
	if responseBody != nil {
		responseResult[toolResponseBodyField] = responseBody
	}
	return responseResult
}

func buildToolResult(output any) *mcp.CallToolResult {
	result := &mcp.CallToolResult{}
	if structuredContent, ok := output.(map[string]any); ok {
		result.StructuredContent = structuredContent
	}
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
	if outputSchema := buildToolOutputSchema(toolConfig, serverName); outputSchema != nil {
		tool.OutputSchema = outputSchema
	}
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
			toolHandler := genToolHandler(toolConfig)
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
		toolHandler := genToolHandler(toolConfig)
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
	base        http.RoundTripper
	logger      *zap.SugaredLogger
	appCode     string
	username    string
	requestID   string
	xRequestID  string
	gatewayName string
	toolName    string
}

func buildLoggingTransport(
	ctx context.Context,
	baseTransport http.RoundTripper,
	toolApiConfig *ToolConfig,
	appCode, username, requestID, xRequestID string,
) *loggingTransport {
	return &loggingTransport{
		base:        baseTransport,
		logger:      logging.GetLogger(),
		appCode:     appCode,
		username:    username,
		requestID:   requestID,
		xRequestID:  xRequestID,
		gatewayName: util.GetGatewayNameFromContext(ctx),
		toolName:    toolApiConfig.String(),
	}
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
			semconv.HTTPURLKey.String(req.URL.Path),
			semconv.HTTPHostKey.String(req.Host),
			attribute.String("mcp.tool_name", t.toolName),
		)
		// Inject trace context (W3C traceparent/tracestate) into outgoing HTTP headers
		// so downstream services can continue the trace.
		otel.GetTextMapPropagator().Inject(ctx, propagation.HeaderCarrier(req.Header))
		req = req.WithContext(ctx)
	}

	// 记录请求日志
	t.logger.Infow("outgoing request",
		"app_code", t.appCode,
		"bk_username", t.username,
		"request_id", t.requestID,
		"x_request_id", t.xRequestID,
		"gateway_name", t.gatewayName,
		"tool", t.toolName,
		"method", req.Method,
		"url", req.URL.Path,
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
			"bk_username", t.username,
			"request_id", t.requestID,
			"x_request_id", t.xRequestID,
			"gateway_name", t.gatewayName,
			"tool", t.toolName,
			"method", req.Method,
			"url", req.URL.Path,
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
		"bk_username", t.username,
		"request_id", t.requestID,
		"x_request_id", t.xRequestID,
		"gateway_name", t.gatewayName,
		"tool", t.toolName,
		"method", req.Method,
		"url", req.URL.Path,
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
		clientIP := util.GetClientIPFromContext(ctx)

		// 在所有日志中添加 app_code, username 和 client_ip
		auditLog = auditLog.With(
			zap.String("tool", toolApiConfig.String()),
			zap.String("app_code", appCode),
			zap.String("bk_username", username),
			zap.String("client_ip", clientIP),
		)
		// 延迟签发 inner JWT - 只有在调用外部 API 时才签发
		innerJwt, err := util.SignInnerJWTFromContext(ctx)
		if err != nil {
			auditLog.Error("sign inner jwt err", zap.Error(err))
			return nil, trace.WrapErrorWithTraceID(ctx, fmt.Errorf("sign inner jwt failed: %w", err))
		}
		auditLog.Info("call tool", zap.String("request", truncateJSON(req.Params.Arguments, auditLogMaxBodySize)))
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
		// 使用共享的 HTTP Transport 连接池，避免每次 tool call 创建新连接
		logTransport := buildLoggingTransport(
			ctx,
			sharedTransport,
			toolApiConfig,
			appCode,
			username,
			requestID,
			xRequestID,
		)
		client := &http.Client{Transport: logTransport}
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
			for key, value := range headers {
				_ = req.SetHeaderParam(key, value)
				headerInfo[key] = value
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
					var res any
					if response.Body() != nil {
						if e := consumer.Consume(response.Body(), &res); e != nil {
							return nil, e
						}
					}
					responseResult := buildToolResponseEnvelope(
						response.Code(),
						response.GetHeader(constant.BkGatewayRequestIDKey),
						trace.GetTraceIDFromContext(ctx),
						res,
					)
					if response.Code() < 200 || response.Code() > 299 {
						return nil, runtime.NewAPIError("call tool err", responseResult, response.Code())
					}
					return responseResult, nil
				},
			),
		}
		auditLog.Info("call tool request params",
			zap.Any("header", maskSensitiveHeaders(headerInfo)),
			zap.Any("query", handlerRequest.QueryParam),
			zap.Any("path", handlerRequest.PathParam),
			zap.String("body", truncateJSON(handlerRequest.BodyParam, auditLogMaxBodySize)),
		)
		openAPIClient := cli.New(toolApiConfig.Host, toolApiConfig.BasePath, []string{toolApiConfig.Schema})
		submit, err := openAPIClient.Submit(operation)
		if err != nil {
			msg := fmt.Sprintf("call %s error:%s", toolApiConfig, err.Error())
			auditLog.Error("call tool err", zap.Any("header", maskSensitiveHeaders(headerInfo)), zap.Error(err))
			if span != nil {
				span.SetStatus(codes.Error, msg)
				span.RecordError(err)
			}
			// Append trace_id to the error message for traceability
			// Skip if err is APIError, since responseResult already contains trace_id
			if _, ok := err.(*runtime.APIError); !ok {
				if traceID := trace.GetTraceIDFromContext(ctx); traceID != "" {
					msg = fmt.Sprintf("%s (trace_id=%s)", msg, traceID)
				}
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
			zap.String("response", truncateJSON(submit, auditLogMaxResponseSize)),
			zap.Any("header", maskSensitiveHeaders(headerInfo)))
		return buildToolResult(submit), nil
	}
	return handler
}
