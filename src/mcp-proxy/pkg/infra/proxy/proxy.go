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
	"log"
	"net/http"
	"sync"

	"github.com/getkin/kin-openapi/openapi3"
	"github.com/gin-gonic/gin"
	"github.com/go-openapi/runtime"
	cli "github.com/go-openapi/runtime/client"
	"github.com/go-openapi/runtime/logger"
	"github.com/go-openapi/strfmt"
	"github.com/modelcontextprotocol/go-sdk/mcp"
	"github.com/spf13/cast"
	"go.uber.org/zap"

	"mcp_proxy/pkg/constant"
	"mcp_proxy/pkg/infra/logging"
	"mcp_proxy/pkg/util"
)

// MCPProxy ...
type MCPProxy struct {
	mcpServers map[string]*MCPServer
	rwLock     *sync.RWMutex
	// 运行的mcp server
	activeMCPServers map[string]struct{}
	// message url prefix
	messageUrlFormat string
}

// NewMCPProxy ...
func NewMCPProxy(messageUrlFormat string) *MCPProxy {
	return &MCPProxy{
		mcpServers:       map[string]*MCPServer{},
		rwLock:           &sync.RWMutex{},
		activeMCPServers: map[string]struct{}{},
		messageUrlFormat: messageUrlFormat,
	}
}

// AddMCPServer ...
func (m *MCPProxy) AddMCPServer(name string, mcpServer *MCPServer) {
	m.rwLock.Lock()
	defer m.rwLock.Unlock()
	log.Printf("add mcp server: %s\n", name)
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
		mcpServer := NewMCPServer(config.Name, config.ResourceVersionID)
		// register tool
		for _, toolConfig := range config.Tools {
			bytes, _ := toolConfig.ParamSchema.JSONSchemaBytes()
			tool := &mcp.Tool{
				Name:        toolConfig.Name,
				Description: toolConfig.Description,
				InputSchema: json.RawMessage(bytes),
			}
			toolHandler := genToolHandler(toolConfig)
			mcpServer.RegisterTool(tool, toolHandler)
		}
		// 创建 SSE Handler
		sseHandler := mcp.NewSSEHandler(func(r *http.Request) *mcp.Server {
			return mcpServer.Server
		}, nil)
		mcpServer.SetHandler(sseHandler)
		m.AddMCPServer(config.Name, mcpServer)
	}
	return nil
}

// AddMCPServerFromOpenAPISpec nolint:gofmt
func (m *MCPProxy) AddMCPServerFromOpenAPISpec(name string,
	resourceVersionID int, openAPISpec *openapi3.T, operationIDList []string,
) error {
	operationIDMap := make(map[string]struct{})
	for _, operationID := range operationIDList {
		operationIDMap[operationID] = struct{}{}
	}
	mcpServer := NewMCPServer(name, resourceVersionID)
	mcpServerConfig := &MCPServerConfig{
		Name:              name,
		Tools:             OpenapiToMcpToolConfig(openAPISpec, operationIDMap),
		ResourceVersionID: resourceVersionID,
	}
	// register tool
	for _, toolConfig := range mcpServerConfig.Tools {
		bytes, _ := toolConfig.ParamSchema.JSONSchemaBytes()
		tool := &mcp.Tool{
			Name:        toolConfig.Name,
			Description: toolConfig.Description,
			InputSchema: json.RawMessage(bytes),
		}
		toolHandler := genToolHandler(toolConfig)
		mcpServer.RegisterTool(tool, toolHandler)
	}
	// 创建 SSE Handler
	sseHandler := mcp.NewSSEHandler(func(r *http.Request) *mcp.Server {
		return mcpServer.Server
	}, nil)
	mcpServer.SetHandler(sseHandler)
	m.AddMCPServer(name, mcpServer)
	return nil
}

// UpdateMCPServerFromOpenApiSpec nolint:gofmt
func (m *MCPProxy) UpdateMCPServerFromOpenApiSpec(
	mcpServer *MCPServer, name string, resourceVersionID int, openAPISpec *openapi3.T, operationIDList []string,
) error {
	operationIDMap := make(map[string]struct{})
	for _, operationID := range operationIDList {
		operationIDMap[operationID] = struct{}{}
	}
	mcpServerConfig := &MCPServerConfig{
		Name:  name,
		Tools: OpenapiToMcpToolConfig(openAPISpec, operationIDMap),
	}
	// update tool
	for _, toolConfig := range mcpServerConfig.Tools {
		bytes, _ := toolConfig.ParamSchema.JSONSchemaBytes()
		tool := &mcp.Tool{
			Name:        toolConfig.Name,
			Description: toolConfig.Description,
			InputSchema: json.RawMessage(bytes),
		}
		toolHandler := genToolHandler(toolConfig)
		mcpServer.RegisterTool(tool, toolHandler)
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
			log.Printf("name %s does not exist\n", name)
			return
		}
		if mcpServer.Handler != nil {
			mcpServer.Handler.ServeHTTP(c.Writer, c.Request)
		}
	}
}

// SseMessageHandler ...
// Note: 官方 SDK 的 SSEHandler 会自动处理 message，不需要单独的 message handler
func (m *MCPProxy) SseMessageHandler() gin.HandlerFunc {
	return func(c *gin.Context) {
		name := c.Param("name")
		mcpServer := m.GetMCPServer(name)
		if mcpServer == nil {
			util.BadRequestErrorJSONResponse(c, fmt.Sprintf("mcp server name %s does not exist", name))
			log.Printf("name %s does not exist\n", name)
			return
		}
		if mcpServer.Handler != nil {
			mcpServer.Handler.ServeHTTP(c.Writer, c.Request)
		}
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
		mcpServer.RegisterPrompt(prompt, handler)
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
			mcpServer.UnregisterPrompt(existingPrompt)
		}
	}
	// 注册新的 prompts
	for _, promptConfig := range prompts {
		prompt, handler := genPromptAndHandler(promptConfig)
		mcpServer.RegisterPrompt(prompt, handler)
	}
}

func genPromptAndHandler(promptConfig *PromptConfig) (*mcp.Prompt, mcp.PromptHandler) {
	prompt := &mcp.Prompt{
		Name:        promptConfig.Name,
		Description: promptConfig.Description,
	}
	handler := func(ctx context.Context, request *mcp.GetPromptRequest) (*mcp.GetPromptResult, error) {
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

func genToolHandler(toolApiConfig *ToolConfig) mcp.ToolHandler {
	// 生成handler
	handler := func(ctx context.Context, request *mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		auditLog := logging.GetAuditLoggerWithContext(ctx)
		requestID := util.GetRequestIDFromContext(ctx)
		auditLog = auditLog.With(zap.String("tool", toolApiConfig.String()))
		innerJwt := util.GetInnerJWTTokenFromContext(ctx)
		auditLog.Info("call tool", zap.Any("request", request.Params.Arguments))
		var handlerRequest HandlerRequest
		err := json.Unmarshal(request.Params.Arguments, &handlerRequest)
		if err != nil {
			auditLog.Error("unmarshal handler request err", zap.String("request",
				string(request.Params.Arguments)), zap.Error(err))
			return nil, err
		}
		tr := &http.Transport{
			TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
		}
		client := &http.Client{Transport: tr}
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
		openAPIClient.SetLogger(logger.StandardLogger{})
		submit, err := openAPIClient.Submit(operation)
		if err != nil {
			msg := fmt.Sprintf("call %s error:%s\n", toolApiConfig, err.Error())
			auditLog.Error("call tool err", zap.Any("header", headerInfo), zap.Error(err))
			log.Println(msg)
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
		log.Printf("call %s result: %s\n", toolApiConfig, submit)
		auditLog.Info("call tool", zap.Any("response", submit), zap.Any("header", headerInfo))
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
