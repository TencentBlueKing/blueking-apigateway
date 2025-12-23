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

package proxy

import (
	"context"
	"net/http"
	"sync"

	"github.com/ThinkInAIXYZ/go-mcp/protocol"
	"github.com/ThinkInAIXYZ/go-mcp/server"
	"github.com/ThinkInAIXYZ/go-mcp/transport"

	"mcp_proxy/pkg/constant"
	"mcp_proxy/pkg/util"
)

// MCPServer ...
type MCPServer struct {
	Server                *server.Server
	Transport             transport.ServerTransport
	SSEHandler            *transport.SSEHandler            // SSE 协议 Handler
	StreamableHTTPHandler *transport.StreamableHTTPHandler // Streamable HTTP 协议 Handler
	protocolType          string                           // 协议类型: sse 或 streamable_http
	name                  string
	// 生效的资源版本号
	resourceVersionID int
	tools             map[string]struct{}
	prompts           map[string]struct{}
	rwLock            *sync.RWMutex
}

// NewMCPServer 创建 SSE 协议的 MCP Server
func NewMCPServer(
	transport transport.ServerTransport,
	handler *transport.SSEHandler,
	name string,
	resourceVersion int,
) *MCPServer {
	mcpServer, err := server.NewServer(transport)
	if err != nil {
		panic(err)
	}
	return &MCPServer{
		Server:            mcpServer,
		Transport:         transport,
		SSEHandler:        handler,
		protocolType:      constant.MCPServerProtocolTypeSSE,
		tools:             make(map[string]struct{}),
		prompts:           make(map[string]struct{}),
		rwLock:            &sync.RWMutex{},
		name:              name,
		resourceVersionID: resourceVersion,
	}
}

// NewStreamableHTTPMCPServer 创建 Streamable HTTP 协议的 MCP Server
func NewStreamableHTTPMCPServer(
	trans transport.ServerTransport,
	handler *transport.StreamableHTTPHandler,
	name string,
	resourceVersion int,
) *MCPServer {
	mcpServer, err := server.NewServer(trans)
	if err != nil {
		panic(err)
	}
	return &MCPServer{
		Server:                mcpServer,
		Transport:             trans,
		StreamableHTTPHandler: handler,
		protocolType:          constant.MCPServerProtocolTypeStreamableHTTP,
		tools:                 make(map[string]struct{}),
		prompts:               make(map[string]struct{}),
		rwLock:                &sync.RWMutex{},
		name:                  name,
		resourceVersionID:     resourceVersion,
	}
}

// GetProtocolType 获取协议类型
func (s *MCPServer) GetProtocolType() string {
	return s.protocolType
}

// IsStreamableHTTP 判断是否为 Streamable HTTP 协议
func (s *MCPServer) IsStreamableHTTP() bool {
	return s.protocolType == constant.MCPServerProtocolTypeStreamableHTTP
}

// HandleSSE 返回 SSE 连接 Handler
func (s *MCPServer) HandleSSE() http.Handler {
	if s.SSEHandler != nil {
		return s.SSEHandler.HandleSSE()
	}
	return nil
}

// HandleMessage 返回 SSE 消息 Handler
func (s *MCPServer) HandleMessage() http.Handler {
	if s.SSEHandler != nil {
		return s.SSEHandler.HandleMessage()
	}
	return nil
}

// HandleMCP 返回 Streamable HTTP Handler
func (s *MCPServer) HandleMCP() http.Handler {
	if s.StreamableHTTPHandler != nil {
		return s.StreamableHTTPHandler.HandleMCP()
	}
	return nil
}

// IsRegisteredTool checks if the tool is registered
func (s *MCPServer) IsRegisteredTool(toolName string) bool {
	s.rwLock.RLock()
	defer s.rwLock.RUnlock()
	_, ok := s.tools[toolName]
	return ok
}

// GetResourceVersionID returns the resource version id ...
func (s *MCPServer) GetResourceVersionID() int {
	s.rwLock.RLock()
	defer s.rwLock.RUnlock()
	return s.resourceVersionID
}

// SetResourceVersionID sets the resource version id ...
func (s *MCPServer) SetResourceVersionID(version int) {
	s.rwLock.Lock()
	defer s.rwLock.Unlock()
	s.resourceVersionID = version
}

// GetTools ...
func (s *MCPServer) GetTools() []string {
	s.rwLock.RLock()
	defer s.rwLock.RUnlock()
	toolNames := make([]string, 0, len(s.tools))
	for toolName := range s.tools {
		toolNames = append(toolNames, toolName)
	}
	return toolNames
}

// Run ...
func (s *MCPServer) Run(ctx context.Context) {
	util.GoroutineWithRecovery(ctx, func() {
		if err := s.Server.Run(); err != nil {
			panic(err)
		}
	})
}

// Shutdown ...
func (s *MCPServer) Shutdown(ctx context.Context) {
	util.GoroutineWithRecovery(ctx, func() {
		if err := s.Server.Shutdown(ctx); err != nil {
			panic(err)
		}
	})
}

// RegisterTool ...
func (s *MCPServer) RegisterTool(tool *protocol.Tool, toolHandler server.ToolHandlerFunc) {
	s.Server.RegisterTool(tool, toolHandler)
	s.rwLock.Lock()
	defer s.rwLock.Unlock()
	s.tools[tool.Name] = struct{}{}
}

// UnregisterTool  unregisters a tool from the server
func (s *MCPServer) UnregisterTool(toolName string) {
	s.Server.UnregisterTool(toolName)
	s.rwLock.Lock()
	defer s.rwLock.Unlock()
	delete(s.tools, toolName)
}

// RegisterResources ...
func (s *MCPServer) RegisterResources(resource *protocol.Resource, resourceHandler server.ResourceHandlerFunc) {
	s.Server.RegisterResource(resource, resourceHandler)
}

// RegisterPrompt registers a prompt to the server
func (s *MCPServer) RegisterPrompt(prompt *protocol.Prompt, promptHandler server.PromptHandlerFunc) {
	s.Server.RegisterPrompt(prompt, promptHandler)
	s.rwLock.Lock()
	defer s.rwLock.Unlock()
	s.prompts[prompt.Name] = struct{}{}
}

// UnregisterPrompt unregisters a prompt from the server
func (s *MCPServer) UnregisterPrompt(promptName string) {
	s.Server.UnregisterPrompt(promptName)
	s.rwLock.Lock()
	defer s.rwLock.Unlock()
	delete(s.prompts, promptName)
}

// GetPromptNames returns all registered prompt names
func (s *MCPServer) GetPromptNames() []string {
	s.rwLock.RLock()
	defer s.rwLock.RUnlock()
	promptNames := make([]string, 0, len(s.prompts))
	for promptName := range s.prompts {
		promptNames = append(promptNames, promptName)
	}
	return promptNames
}

// IsRegisteredPrompt checks if the prompt is registered
func (s *MCPServer) IsRegisteredPrompt(promptName string) bool {
	s.rwLock.RLock()
	defer s.rwLock.RUnlock()
	_, ok := s.prompts[promptName]
	return ok
}
