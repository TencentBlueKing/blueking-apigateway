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

	"github.com/TencentBlueKing/gopkg/stringx"
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

	"mcp_proxy/pkg/cacheimpls"
	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/constant"
	"mcp_proxy/pkg/infra/logging"
	"mcp_proxy/pkg/infra/trace"
	"mcp_proxy/pkg/metric"
	"mcp_proxy/pkg/util"
)

const (
	toolResponseStatusCodeField = "status_code"
	toolResponseRequestIDField  = "request_id"
	toolResponseTraceIDField    = "trace_id"
	toolResponseXRequestIDField = "x_request_id"
	toolResponseBodyField       = "response_body"
)

// sharedTransport 是所有 tool call 共用的 HTTP Transport，避免每次调用创建新连接池。
// 通过 InitSharedTransport 从配置初始化，参数可在 config.yaml 的 mcpServer.transport 段调整。
var (
	sharedTransport     *http.Transport
	sharedTransportOnce sync.Once
)

// InitSharedTransport initializes the shared HTTP Transport from config.
// It is safe for concurrent use: only the first call takes effect, subsequent calls are no-ops.
// nolint:gosec
func InitSharedTransport(cfg config.Transport) {
	sharedTransportOnce.Do(func() {
		sharedTransport = &http.Transport{
			// NOTE: InsecureSkipVerify 跳过 TLS 证书验证，仅在内部网络环境下使用。
			// 公网环境请在 config.yaml 中设置 mcpServer.transport.insecureSkipVerify: false。
			TLSClientConfig:     &tls.Config{InsecureSkipVerify: cfg.InsecureSkipVerify},
			MaxIdleConns:        cfg.MaxIdleConns,
			MaxIdleConnsPerHost: cfg.MaxIdleConnsPerHost,
			IdleConnTimeout:     time.Duration(cfg.IdleConnTimeoutSecond) * time.Second,
		}
	})
}

// MCPProxy ...
type MCPProxy struct {
	mcpServers map[string]*MCPServer
	rwLock     *sync.RWMutex
	// 运行的mcp server
	activeMCPServers map[string]struct{}
	// sseUserPublicPathPrefix / sseAppPublicPathPrefix: gateway-facing path prefixes prepended to
	// req.URL.Path before SSEHandler so the endpoint event matches clients behind a strip-prefix proxy.
	sseUserPublicPathPrefix string
	sseAppPublicPathPrefix  string
}

// NewMCPProxy creates a proxy. sseUserPublicPathPrefix and sseAppPublicPathPrefix are derived from
// mcpServer.messageUrlFormat and mcpServer.messageApplicationUrlFormat (see config.DerivePublicPathPrefix).
// Use empty strings when there is no gateway prefix (e.g. local tests).
func NewMCPProxy(sseUserPublicPathPrefix, sseAppPublicPathPrefix string) *MCPProxy {
	return &MCPProxy{
		mcpServers:              map[string]*MCPServer{},
		rwLock:                  &sync.RWMutex{},
		activeMCPServers:        map[string]struct{}{},
		sseUserPublicPathPrefix: sseUserPublicPathPrefix,
		sseAppPublicPathPrefix:  sseAppPublicPathPrefix,
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

func buildToolResponseEnvelope(statusCode int, requestID, traceID, xRequestID string, responseBody any) map[string]any {
	responseResult := map[string]any{
		toolResponseStatusCodeField: statusCode,
		toolResponseRequestIDField:  requestID,
		toolResponseTraceIDField:    traceID,
		toolResponseXRequestIDField: xRequestID,
		// Always include response_body to keep consistency with the outputSchema definition.
		// When responseBody is nil, the field will be JSON null, which matches the schema expectation.
		toolResponseBodyField: responseBody,
	}
	return responseResult
}

func buildToolResult(output any) *mcp.CallToolResult {
	result := &mcp.CallToolResult{}
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
				server, httpHandler, config.Name, config.ResourceVersionID, config.RawResponse,
			)
		} else {
			// 默认使用 SSE Handler
			sseHandler := mcp.NewSSEHandler(func(r *http.Request) *mcp.Server {
				return server
			}, nil)
			mcpServer = NewMCPServer(server, sseHandler, config.Name, config.ResourceVersionID, config.RawResponse)
		}

		// register tool
		for _, toolConfig := range config.Tools {
			toolHandler := genToolHandler(toolConfig, config.Name, config.RawResponse)
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
	toolNameMap map[string]string, protocolType string, rawResponse bool,
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
		RawResponse:       rawResponse,
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
		Name:        name,
		Tools:       OpenapiToMcpToolConfig(openAPISpec, operationIDMap, toolNameMap),
		RawResponse: mcpServer.IsRawResponse(),
	}
	// update tool
	for _, toolConfig := range mcpServerConfig.Tools {
		toolHandler := genToolHandler(toolConfig, name, mcpServer.IsRawResponse())
		mcpServer.AddTool(buildMCPTool(toolConfig, name), toolHandler)
	}
	// 更新资源版本号
	mcpServer.SetResourceVersionID(resourceVersionID)
	return nil
}

// SseHandler 用户态 SSE（/:name/sse）。
func (m *MCPProxy) SseHandler() gin.HandlerFunc {
	return m.sseHandlerWithPrefix(m.sseUserPublicPathPrefix)
}

// SseHandlerApplication 应用态 SSE（/:name/application/sse）。
func (m *MCPProxy) SseHandlerApplication() gin.HandlerFunc {
	return m.sseHandlerWithPrefix(m.sseAppPublicPathPrefix)
}

func (m *MCPProxy) sseHandlerWithPrefix(publicPathPrefix string) gin.HandlerFunc {
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
		req := util.RequestWithPublicPathPrefix(c.Request, publicPathPrefix)
		handler.ServeHTTP(c.Writer, req)
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

// CleanupAll deletes all MCP servers and returns their names.
// It acquires the write lock once to avoid repeated lock/unlock per server.
func (m *MCPProxy) CleanupAll() []string {
	m.rwLock.Lock()
	defer m.rwLock.Unlock()

	var names []string
	for name, svr := range m.mcpServers {
		names = append(names, name)
		svr.Shutdown(context.Background())
	}
	m.mcpServers = make(map[string]*MCPServer)
	m.activeMCPServers = make(map[string]struct{})
	return names
}

// CleanupStale deletes MCP servers not in the activeSet and returns deleted names.
// It acquires the write lock once to avoid repeated lock/unlock per server.
func (m *MCPProxy) CleanupStale(activeSet map[string]struct{}) []string {
	m.rwLock.Lock()
	defer m.rwLock.Unlock()

	var deleted []string
	for name, svr := range m.mcpServers {
		if _, ok := activeSet[name]; !ok {
			svr.Shutdown(context.Background())
			delete(m.mcpServers, name)
			delete(m.activeMCPServers, name)
			deleted = append(deleted, name)
		}
	}
	return deleted
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

// setupToolCallSpan creates a trace span for tool call if tracing is enabled.
func setupToolCallSpan(
	ctx context.Context, toolName, toolMethod, toolURL, toolHost string,
) (context.Context, oteltrace.Span) {
	if config.G == nil || !config.G.Tracing.McpAPIEnabled() {
		return ctx, nil
	}
	ctx, span := trace.StartTrace(ctx, fmt.Sprintf("mcp.tool.%s", toolName))
	if span != nil {
		span.SetAttributes(
			attribute.String("mcp.tool_name", toolName),
			attribute.String("mcp.tool_method", toolMethod),
			attribute.String("mcp.tool_url", toolURL),
			attribute.String("mcp.tool_host", toolHost),
		)
	}
	return ctx, span
}

// prepareToolCallAuditLog prepares audit logger with request context information.
func prepareToolCallAuditLog(
	ctx context.Context,
	req *mcp.CallToolRequest,
	toolName, toolConfig string,
) (*zap.Logger, string, string, string, string, string) {
	requestID := util.GetRequestIDFromContext(ctx)
	xRequestID := util.GetXRequestIDFromContext(ctx)
	appCode := util.GetAppCodeFromContext(ctx)
	username := util.GetUsernameFromContext(ctx)
	clientIP := util.GetClientIPFromContext(ctx)

	// Extract request_id and x_request_id from request header if not found in context
	if req != nil {
		if extra := req.GetExtra(); extra != nil && extra.Header != nil {
			if requestID == "" {
				requestID = extra.Header.Get(constant.BkGatewayRequestIDKey)
			}
			if xRequestID == "" {
				xRequestID = extra.Header.Get(constant.RequestIDHeaderKey)
			}
		}
	}

	auditLog := logging.GetAuditLoggerWithContext(ctx).With(
		zap.String("request_id", requestID),
		zap.String("x_request_id", xRequestID),
		zap.String("mcp_method", "tools/call"),
		zap.String("tool_name", toolName),
		zap.String("tool", toolConfig),
		zap.String("app_code", appCode),
		zap.String("bk_username", username),
		zap.String("client_ip", clientIP),
	)

	return auditLog, requestID, xRequestID, appCode, username, clientIP
}

// buildToolCallClient creates HTTP client with shared transport and logging.
func buildToolCallClient(
	ctx context.Context,
	toolApiConfig *ToolConfig,
	appCode, username, requestID, xRequestID string,
) *http.Client {
	logTransport := buildLoggingTransport(
		ctx,
		sharedTransport,
		toolApiConfig,
		appCode,
		username,
		requestID,
		xRequestID,
	)
	return &http.Client{Transport: logTransport}
}

// handleToolCallError handles errors from tool calls and returns appropriate result.
func handleToolCallError(
	ctx context.Context,
	err error,
	toolApiConfig *ToolConfig,
	auditLog *zap.Logger,
	headerInfo map[string]string,
	span oteltrace.Span,
	start time.Time,
) *mcp.CallToolResult {
	msg := fmt.Sprintf("call %s error:%s", toolApiConfig, err.Error())
	duration := time.Since(start)

	auditLog.Error("call tool err",
		zap.Any("header", util.MaskSensitiveHeaders(headerInfo)),
		zap.Error(err),
		zap.String("latency", duration.String()),
		zap.String("status", "failed"),
		zap.Int64("response_body_size", 0),
	)

	if span != nil {
		span.SetStatus(codes.Error, msg)
		span.RecordError(err)
	}

	result := &mcp.CallToolResult{
		Content: []mcp.Content{
			&mcp.TextContent{
				Text: msg,
			},
		},
		IsError: true,
	}

	if _, ok := err.(*runtime.APIError); !ok {
		// For non-APIError, append trace_id to the error message for traceability
		if traceID := trace.GetTraceIDFromContext(ctx); traceID != "" {
			msg = fmt.Sprintf("%s (trace_id=%s)", msg, traceID)
			result.Content = []mcp.Content{
				&mcp.TextContent{
					Text: msg,
				},
			}
		}
	}

	return result
}

func genToolHandler(toolApiConfig *ToolConfig, serverName string, rawResponse bool) ToolHandler {
	// 生成handler
	handler := func(ctx context.Context, req *mcp.CallToolRequest) (result *mcp.CallToolResult, err error) {
		start := time.Now()

		// Start a trace span for the actual upstream tool invocation
		ctx, span := setupToolCallSpan(
			ctx,
			toolApiConfig.Name,
			toolApiConfig.Method,
			toolApiConfig.Url,
			toolApiConfig.Host,
		)
		if span != nil {
			defer span.End()
		}

		// MCP protocol-level logging and metrics
		defer func() {
			if r := recover(); r != nil {
				logging.GetAPILogger().Error("panic in tool handler",
					zap.String("mcp_method", "tools/call"),
					zap.String("tool_name", toolApiConfig.Name),
					zap.Any("panic", r),
					zap.String("server_name", serverName),
				)
				if err == nil {
					err = fmt.Errorf("panic: %v", r)
				}
			}
			recordToolCallMetrics(ctx, serverName, toolApiConfig.Name, req, result, err, start)
			logToolCall(ctx, serverName, toolApiConfig.Name, req, result, err, start)
		}()

		// Prepare audit log with request context
		auditLog, requestID, xRequestID, appCode, username, _ := prepareToolCallAuditLog(
			ctx, req, toolApiConfig.Name, toolApiConfig.String())
		// 延迟签发 inner JWT - 只有在调用外部 API 时才签发
		innerJwt, err := util.SignInnerJWTFromContext(ctx)
		if err != nil {
			auditLog.Error("sign inner jwt err", zap.Error(err))
			return nil, trace.WrapErrorWithTraceID(ctx, fmt.Errorf("sign inner jwt failed: %w", err))
		}
		logTruncate := config.G.McpServer.LogTruncate
		requestBody := util.TruncateJSON(req.Params.Arguments, logTruncate.GetAuditLogMaxBodySize())

		// 用于在 defer 中记录完整的调用信息（包含 response, latency 等）
		var (
			auditResponse      string
			auditResponseSize  int64
			auditLatency       time.Duration
			auditStatus        = "success"
			auditUpstreamReqID string
			auditHeaderInfo    map[string]string
			auditQueryParam    map[string]interface{}
			auditPathParam     map[string]interface{}
			auditBodyParam     interface{}
		)

		// 在函数返回时记录完整的 audit log，包含 response, latency 等字段
		defer func() {
			if r := recover(); r != nil {
				auditStatus = "failed"
			}
			// 记录完整的调用信息（合并了之前的 "call tool" 和 "call tool request params" 日志）
			auditLog.Info("call tool complete",
				zap.String("request", requestBody),
				zap.String("params", requestBody),
				zap.String("response", auditResponse),
				zap.Int64("request_body_size", int64(len(requestBody))),
				zap.Int64("response_body_size", auditResponseSize),
				zap.String("latency", auditLatency.String()),
				zap.String("status", auditStatus),
				zap.String("upstream_request_id", auditUpstreamReqID),
				zap.Any("header", util.MaskSensitiveHeaders(auditHeaderInfo)),
				zap.Any("query", auditQueryParam),
				zap.Any("path", auditPathParam),
				zap.String("body", util.TruncateJSON(auditBodyParam, logTruncate.GetAuditLogMaxBodySize())),
			)
		}()
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
		// Build HTTP client with shared transport
		client := buildToolCallClient(ctx, toolApiConfig, appCode, username, requestID, xRequestID)
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
							trace.GetTraceIDFromContext(ctx),
							xRequestID,
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
		// 保存请求参数，供 defer 中的 "call tool complete" 使用
		auditHeaderInfo = headerInfo
		auditQueryParam = handlerRequest.QueryParam
		auditPathParam = handlerRequest.PathParam
		auditBodyParam = handlerRequest.BodyParam

		openAPIClient := cli.New(toolApiConfig.Host, toolApiConfig.BasePath, []string{toolApiConfig.Schema})
		submit, err := openAPIClient.Submit(operation)
		if err != nil {
			duration := time.Since(start)
			auditResponse = fmt.Sprintf("call %s error:%s", toolApiConfig, err.Error())
			auditResponseSize = 0
			auditLatency = duration
			auditStatus = "failed"
			// nolint:nilerr
			return handleToolCallError(ctx, err, toolApiConfig, auditLog, headerInfo, span, start), nil
		}
		duration := time.Since(start)
		responseBody := util.TruncateJSON(submit, logTruncate.GetAuditLogMaxResponseSize())
		// 设置 audit log 变量，供 defer 中的 "call tool complete" 使用
		auditResponse = responseBody
		auditResponseSize = int64(len(responseBody))
		auditLatency = duration
		auditStatus = "success"
		auditUpstreamReqID = extractUpstreamRequestID(buildToolResult(submit))
		// 注意：完整的调用结果会在 defer 中的 "call tool complete" 日志中记录
		return buildToolResult(submit), nil
	}
	return handler
}

// recordToolCallMetrics records MCP protocol-level metrics for tools/call.
// This is needed because tools/call handler is invoked inside callTool(),
// which does not go through the MCP middleware chain.
func recordToolCallMetrics(
	ctx context.Context,
	serverName, toolName string,
	req *mcp.CallToolRequest,
	result *mcp.CallToolResult,
	err error,
	start time.Time,
) {
	if metric.MCPToolCallTotal == nil {
		return
	}

	duration := time.Since(start)
	// Check both err and result.IsError: MCP framework-level failures (e.g., upstream API errors)
	// are often returned as CallToolResult{IsError: true} with err == nil
	hasError := err != nil || (result != nil && result.IsError)
	gatewayName := util.GetGatewayNameFromContext(ctx)
	appCode := util.GetAppCodeFromContext(ctx)

	// Error code
	errorLabel := "0"
	errorCode := "0"
	if hasError {
		errorLabel = "1"
		errorCode = "unknown"
		// Try to extract jsonrpc error code if available
		// Note: Tool handlers typically don't return jsonrpc errors directly,
		// but we check just in case
	}

	// Record metrics
	metric.MCPRequestTotal.WithLabelValues(gatewayName, serverName, "tools/call", appCode, errorCode, errorLabel).Inc()
	metric.MCPToolCallTotal.WithLabelValues(gatewayName, serverName, toolName, appCode, errorCode, errorLabel).Inc()
	metric.MCPRequestDuration.WithLabelValues(gatewayName, serverName, "tools/call", appCode).
		Observe(duration.Seconds() * 1000)

	if hasError {
		metric.MCPErrorTotal.WithLabelValues(gatewayName, serverName, "tools/call", appCode, errorCode).Inc()
	}

	// Record request/response body size metrics
	if metric.MCPRequestBodySize != nil && metric.MCPResponseBodySize != nil {
		var requestBodySize, responseBodySize int64

		// Calculate request body size from CallToolRequest
		if req != nil && req.Params != nil && req.Params.Arguments != nil {
			if paramsBytes, marshalErr := json.Marshal(req.Params.Arguments); marshalErr == nil {
				requestBodySize = int64(len(paramsBytes))
			}
		}

		// Calculate response body size from CallToolResult
		if result != nil {
			if resultBytes, marshalErr := json.Marshal(result); marshalErr == nil {
				responseBodySize = int64(len(resultBytes))
			}
		}

		metric.MCPRequestBodySize.WithLabelValues(gatewayName, serverName, "tools/call").
			Observe(float64(requestBodySize))
		metric.MCPResponseBodySize.WithLabelValues(gatewayName, serverName, "tools/call").
			Observe(float64(responseBodySize))
	}
}

// logToolCall logs MCP protocol-level request/response for tools/call.
// This is needed because tools/call handler is invoked inside callTool(),
// which does not go through the MCP middleware chain.
func logToolCall(
	ctx context.Context,
	serverName string,
	toolName string,
	req *mcp.CallToolRequest,
	result *mcp.CallToolResult,
	err error,
	start time.Time,
) {
	logger := logging.GetAPILogger()
	duration := time.Since(start)
	// Check both err and result.IsError: MCP framework-level failures (e.g., upstream API errors)
	// are often returned as CallToolResult{IsError: true} with err == nil
	hasError := err != nil || (result != nil && result.IsError)

	// Resolve truncation limits from config
	logTruncate := config.G.McpServer.LogTruncate

	// Serialize request params and response
	params, requestBodySize := serializeToolCallRequest(req, logTruncate)
	response, responseBodySize, upstreamRequestID := serializeToolCallResponse(result, hasError, logTruncate)

	// Retrieve extra info from context
	ctxInfo := extractToolCallContextInfo(ctx, req)

	// Get session info
	sessionID, clientID := extractToolCallSessionInfo(req, ctxInfo.clientID)

	// trace_id from HTTP layer
	traceID := trace.GetTraceIDFromContext(ctx)

	// Build log fields
	status := "success"
	if hasError {
		status = "failed"
	}

	fields := []zap.Field{
		// Trace identifiers
		zap.String("request_id", ctxInfo.requestID),
		zap.String("x_request_id", ctxInfo.xRequestID),
		zap.String("session_id", sessionID),
		// Gateway info
		zap.Int("gateway_id", ctxInfo.gatewayID),
		zap.String("gateway_name", ctxInfo.gatewayName),
		// MCP request info
		zap.String("mcp_server_name", serverName),
		zap.Int("mcp_server_id", ctxInfo.mcpServerID),
		zap.String("mcp_method", "tools/call"),
		// HTTP request info: MCP 协议层不需要展示 HTTP path/method，置空保持字段一致
		zap.String("method", ""),
		zap.String("path", ""),
		// Caller info
		zap.String("app_code", ctxInfo.appCode),
		zap.String("bk_username", ctxInfo.username),
		zap.String("client_ip", ctxInfo.clientIP),
		zap.String("client_id", clientID),
		// Tool specific fields
		zap.String("tool_name", toolName),
		zap.String("prompt_name", ""),
		// Request/Response content
		zap.String("params", params),
		zap.String("response", response),
		// Body sizes
		zap.Int64("request_body_size", requestBodySize),
		zap.Int64("response_body_size", responseBodySize),
		// Performance
		zap.String("latency", duration.String()),
		// Status
		zap.String("status", status),
	}

	// Only append upstream_request_id if non-empty (for traceability)
	if upstreamRequestID != "" {
		fields = append(fields, zap.String("upstream_request_id", upstreamRequestID))
	}

	// Only append trace_id if non-empty
	if traceID != "" {
		fields = append(fields, zap.String("trace_id", traceID))
	}

	if hasError {
		fields = append(fields, zap.Error(err))
	}

	logger.Info("-", fields...)
}

// serializeToolCallRequest serializes the tool call request params.
func serializeToolCallRequest(req *mcp.CallToolRequest, logTruncate config.LogTruncate) (string, int64) {
	if req == nil || req.Params == nil || req.Params.Arguments == nil {
		return "", 0
	}
	paramsBytes, marshalErr := json.Marshal(req.Params.Arguments)
	if marshalErr != nil {
		return "", 0
	}
	requestBodySize := int64(len(paramsBytes))
	params := stringx.Truncate(string(paramsBytes), logTruncate.GetAPILogRequestSize())
	return params, requestBodySize
}

// serializeToolCallResponse serializes the tool call response result.
func serializeToolCallResponse(
	result *mcp.CallToolResult,
	hasError bool,
	logTruncate config.LogTruncate,
) (string, int64, string) {
	if result == nil {
		return "", 0, ""
	}
	resultBytes, marshalErr := json.Marshal(result)
	if marshalErr != nil {
		return "", 0, ""
	}
	responseBodySize := int64(len(resultBytes))
	var response string
	if hasError {
		response = stringx.Truncate(string(resultBytes), logTruncate.GetAPILogErrorResponseSize())
	} else {
		response = stringx.Truncate(string(resultBytes), logTruncate.GetAPILogResponseSize())
	}
	upstreamRequestID := extractUpstreamRequestID(result)
	return response, responseBodySize, upstreamRequestID
}

// toolCallContextInfo holds context-derived info for tool call logging.
type toolCallContextInfo struct {
	requestID   string
	xRequestID  string
	gatewayID   int
	gatewayName string
	mcpServerID int
	appCode     string
	username    string
	clientIP    string
	clientID    string
}

// extractToolCallContextInfo extracts gateway, request, and caller info from context and request headers.
func extractToolCallContextInfo(ctx context.Context, req *mcp.CallToolRequest) toolCallContextInfo {
	info := toolCallContextInfo{
		gatewayID:   util.GetGatewayIDFromContext(ctx),
		gatewayName: util.GetGatewayNameFromContext(ctx),
		mcpServerID: util.GetMCPServerIDFromContext(ctx),
		requestID:   util.GetRequestIDFromContext(ctx),
		xRequestID:  util.GetXRequestIDFromContext(ctx),
		appCode:     util.GetAppCodeFromContext(ctx),
		username:    util.GetUsernameFromContext(ctx),
		clientIP:    util.GetClientIPFromContext(ctx),
		clientID:    util.GetClientIDFromContext(ctx),
	}

	// Extract X-Request-ID from request header if not found in context
	if info.xRequestID == "" && req != nil {
		if extra := req.GetExtra(); extra != nil && extra.Header != nil {
			info.xRequestID = extra.Header.Get(constant.RequestIDHeaderKey)
		}
	}

	// Extract X-Bkapi-Request-ID from request header if not found in context
	if info.requestID == "" && req != nil {
		if extra := req.GetExtra(); extra != nil && extra.Header != nil {
			info.requestID = extra.Header.Get(constant.BkGatewayRequestIDKey)
		}
	}

	// Try to get gateway_name from cache if not found in context
	if info.gatewayName == "" && info.gatewayID > 0 {
		if gw, err := cacheimpls.GetGatewayByID(ctx, info.gatewayID); err == nil && gw != nil {
			info.gatewayName = gw.Name
		}
	}

	return info
}

// extractToolCallSessionInfo extracts session ID and client_id from the MCP session.
func extractToolCallSessionInfo(req *mcp.CallToolRequest, clientID string) (string, string) {
	if req == nil {
		return "", clientID
	}
	var sessionID string
	if ss, ok := req.GetSession().(*mcp.ServerSession); ok && ss != nil {
		sessionID = ss.ID()
		// Enrich client_id with clientInfo from initialize handshake
		if initParams := ss.InitializeParams(); initParams != nil && initParams.ClientInfo != nil {
			clientID = initParams.ClientInfo.Name
		}
	}
	return sessionID, clientID
}

// extractUpstreamRequestID extracts the upstream API request_id from tool call result.
// This is the request_id returned by the upstream API (e.g., bk-apigateway),
// which may differ from the MCP Proxy's own request_id.
func extractUpstreamRequestID(result *mcp.CallToolResult) string {
	if result == nil || len(result.Content) == 0 {
		logging.GetLogger().Debug("extractUpstreamRequestID: result is nil or content is empty")
		return ""
	}

	logging.GetLogger().Debug("extractUpstreamRequestID: content count", zap.Int("count", len(result.Content)))

	// Try to get text content from result
	var textContent string
	for i, content := range result.Content {
		if text, ok := content.(*mcp.TextContent); ok && text != nil {
			textContent = text.Text
			logging.GetLogger().Debug("extractUpstreamRequestID: found TextContent",
				zap.Int("index", i), zap.Int("text_length", len(textContent)))
			break
		} else {
			logging.GetLogger().Debug("extractUpstreamRequestID: content type mismatch",
				zap.Int("index", i), zap.String("type", fmt.Sprintf("%T", content)))
		}
	}
	if textContent == "" {
		logging.GetLogger().Debug("extractUpstreamRequestID: textContent is empty")
		return ""
	}

	// Parse JSON to extract request_id
	var envelope map[string]any
	if err := json.Unmarshal([]byte(textContent), &envelope); err != nil {
		preview := textContent
		if len(textContent) > 200 {
			preview = textContent[:200]
		}
		logging.GetLogger().Debug("extractUpstreamRequestID: failed to unmarshal textContent",
			zap.Error(err), zap.String("text_content_preview", preview))
		return ""
	}

	logging.GetLogger().Debug("extractUpstreamRequestID: envelope keys", zap.Any("keys", getMapKeys(envelope)))

	if requestID, ok := envelope[toolResponseRequestIDField].(string); ok {
		logging.GetLogger().Debug("extractUpstreamRequestID: found request_id", zap.String("request_id", requestID))
		return requestID
	}
	logging.GetLogger().Debug("extractUpstreamRequestID: request_id not found or not a string")
	return ""
}

// getMapKeys returns all keys in a map
func getMapKeys(m map[string]any) []string {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	return keys
}
