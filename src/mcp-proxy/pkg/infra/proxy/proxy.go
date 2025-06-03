/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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

package proxy

import (
	"context"
	"crypto/tls"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"sync"

	"github.com/ThinkInAIXYZ/go-mcp/protocol"
	"github.com/ThinkInAIXYZ/go-mcp/server"
	"github.com/ThinkInAIXYZ/go-mcp/transport"
	"github.com/getkin/kin-openapi/openapi3"
	"github.com/gin-gonic/gin"
	"github.com/go-openapi/runtime"
	cli "github.com/go-openapi/runtime/client"
	"github.com/go-openapi/runtime/logger"
	"github.com/go-openapi/strfmt"
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
	log.Printf("add mcp server: %s\n", name)
	m.mcpServers[name] = mcpServer
}

// GetActiveMCPServerNames ...
func (m *MCPProxy) GetActiveMCPServerNames() []string {
	m.rwLock.Lock()
	defer m.rwLock.Unlock()
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
		trans, sseHandler, err := transport.NewSSEServerTransportAndHandler(
			fmt.Sprintf("/%s/sse/message", config.Name))
		if err != nil {
			return err
		}
		mcpServer := NewMCPServer(trans, sseHandler, config.Name)
		// register tool
		for _, toolConfig := range config.Tools {
			bytes, _ := toolConfig.ParamSchema.JSONSchemaBytes()
			tool := protocol.NewToolWithRawSchema(toolConfig.Name, toolConfig.Description, bytes)
			toolHandler := genToolHandler(toolConfig)
			mcpServer.RegisterTool(tool, toolHandler)
		}
		m.AddMCPServer(config.Name, mcpServer)
	}
	return nil
}

// AddMCPServerFromOpenApiSpec nolint:gofmt
func (m *MCPProxy) AddMCPServerFromOpenApiSpec(name string, openApiSpec *openapi3.T,
	operationIDMap map[string]struct{},
) error {
	mcpServerConfig := &MCPServerConfig{
		Name:  name,
		Tools: OpenapiToMcpToolConfig(openApiSpec, operationIDMap),
	}
	return m.AddMCPServerFromConfigs([]*MCPServerConfig{mcpServerConfig})
}

// SseHandler ...
func (m *MCPProxy) SseHandler() gin.HandlerFunc {
	return func(c *gin.Context) {
		name := c.Param("name")
		if _, ok := m.mcpServers[name]; !ok {
			util.BadRequestErrorJSONResponse(c, fmt.Sprintf("mcp server name %s does not exist", name))
			log.Printf("name %s does not exist\n", name)
			return
		}
		m.mcpServers[name].Handler.HandleSSE().ServeHTTP(c.Writer, c.Request)
	}
}

// SseMessageHandler ...
func (m *MCPProxy) SseMessageHandler() gin.HandlerFunc {
	return func(c *gin.Context) {
		name := c.Param("name")
		if _, ok := m.mcpServers[name]; !ok {
			util.BadRequestErrorJSONResponse(c, fmt.Sprintf("mcp server name %s does not exist", name))
			log.Printf("name %s does not exist\n", name)
			return
		}
		m.mcpServers[name].Handler.HandleMessage().ServeHTTP(c.Writer, c.Request)
	}
}

// Run ...
func (m *MCPProxy) Run(ctx context.Context) {
	m.rwLock.RLock()
	defer m.rwLock.RUnlock()
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

func genToolHandler(toolApiConfig *ToolConfig) server.ToolHandlerFunc {
	// 生成handler
	handler := func(ctx context.Context, request *protocol.CallToolRequest) (*protocol.CallToolResult, error) {
		auditLog := logging.GetAuditLoggerWithContext(ctx)
		auditLog = auditLog.With(zap.String("tool", toolApiConfig.String()))
		innerJwt := util.GetInnerJWTTokenFromContext(ctx)
		auditLog.Info("call tool", zap.Any("request", request.RawArguments))
		var handlerRequest HandlerRequest
		err := json.Unmarshal(request.RawArguments, &handlerRequest)
		if err != nil {
			auditLog.Error("unmarshal handler request err", zap.String("request",
				string(request.RawArguments)), zap.Error(err))
			return nil, err
		}
		tr := &http.Transport{
			TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
		}
		client := http.DefaultClient
		client.Timeout = util.GetBkApiTimeout(ctx)
		client.Transport = tr
		requestParam := runtime.ClientRequestWriterFunc(func(req runtime.ClientRequest, _ strfmt.Registry) error {
			// 设置innerJwt
			err = req.SetHeaderParam(constant.BkApiAuthorizationHeaderKey, innerJwt)
			if err != nil {
				auditLog.Error("set header param err",
					zap.String(constant.BkApiAuthorizationHeaderKey, innerJwt), zap.Error(err))
				return err
			}

			if handlerRequest.HeaderParam != nil {
				for k, v := range handlerRequest.HeaderParam {
					err = req.SetHeaderParam(k, v)
					if err != nil {
						auditLog.Error("set header param err", zap.String(k, v), zap.Error(err))
						return err
					}
				}
			}
			if handlerRequest.QueryParam != nil {
				for k, v := range handlerRequest.QueryParam {
					err = req.SetQueryParam(k, v) // 使用 SetQueryParam 方法设置查询参数
					if err != nil {
						auditLog.Error("set query param err", zap.String(k, v), zap.Error(err))
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
				if err != nil {
					err = req.SetBodyParam(handlerRequest.BodyParam)
					if err != nil {
						auditLog.Error("set body param err",
							zap.Any("body", handlerRequest.BodyParam), zap.Error(err))
						return err
					}
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
					if response.Code() < 200 || response.Code() > 299 {
						return nil, runtime.NewAPIError("call tool err", fmt.Sprintf("%s",
							toolApiConfig),
							response.Code())
					}
					var res map[string]any
					if e := consumer.Consume(response.Body(), &res); e != nil {
						return nil, e
					}
					marshal, _ := json.Marshal(res)
					return string(marshal), nil
				},
			),
		}
		openAPIClient := cli.New(toolApiConfig.Host, toolApiConfig.BasePath, []string{toolApiConfig.Schema})
		openAPIClient.SetLogger(logger.StandardLogger{})
		submit, err := openAPIClient.Submit(operation)
		if err != nil {
			msg := fmt.Sprintf("call %s error:%s\n", toolApiConfig, err.Error())
			auditLog.Error("call tool err", zap.Error(err))
			log.Println(msg)
			// nolint:nilerr
			return &protocol.CallToolResult{
				Content: []protocol.Content{
					&protocol.TextContent{
						Type: "text",
						Text: msg,
					},
				},
				IsError: true,
			}, nil
		}
		log.Printf("call %s result: %s\n", toolApiConfig, submit)
		auditLog.Info("call tool", zap.String("response", submit.(string)))
		return &protocol.CallToolResult{
			Content: []protocol.Content{
				&protocol.TextContent{
					Type: "text",
					Text: submit.(string),
				},
			},
		}, nil
	}
	return handler
}
