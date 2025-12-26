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

	"github.com/modelcontextprotocol/go-sdk/mcp"

	"mcp_proxy/pkg/constant"
)

// ToolHandler is the handler type for tools
type ToolHandler = mcp.ToolHandler

// PromptHandler is the handler type for prompts
type PromptHandler = mcp.PromptHandler

// MCPServer ...
type MCPServer struct {
	Server                *mcp.Server
	SSEHandler            *mcp.SSEHandler            // SSE 协议 Handler
	StreamableHTTPHandler *mcp.StreamableHTTPHandler // Streamable HTTP 协议 Handler
	protocolType          string                     // 协议类型: sse 或 streamable_http
	name                  string
	// 生效的资源版本号
	resourceVersionID int
	tools             map[string]struct{}
	prompts           map[string]struct{}
	rwLock            *sync.RWMutex
}

// NewMCPServer 创建 SSE 协议的 MCP Server
func NewMCPServer(
	server *mcp.Server,
	handler *mcp.SSEHandler,
	name string,
	resourceVersion int,
) *MCPServer {
	return &MCPServer{
		Server:            server,
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
	server *mcp.Server,
	handler *mcp.StreamableHTTPHandler,
	name string,
	resourceVersion int,
) *MCPServer {
	return &MCPServer{
		Server:                server,
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
		return s.SSEHandler
	}
	return nil
}

// HandleMCP 返回 Streamable HTTP Handler
func (s *MCPServer) HandleMCP() http.Handler {
	if s.StreamableHTTPHandler != nil {
		return s.StreamableHTTPHandler
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

// Run starts the MCP server.
// Note: 官方 SDK 的 Server.Run 用于单连接场景（如 stdio），
// 对于 SSE/HTTP 多连接场景，连接由 SSEHandler 管理，此方法为空实现。
func (s *MCPServer) Run(ctx context.Context) {
	// SSE 场景下，连接由 SSEHandler 在 HTTP 请求时自动建立和管理
	// 不需要单独启动 Server
}

// Shutdown gracefully shuts down the MCP server by closing all active sessions.
func (s *MCPServer) Shutdown(ctx context.Context) {
	// 关闭所有活跃的会话
	for session := range s.Server.Sessions() {
		_ = session.Close()
	}
}

// AddTool adds a tool to the server
func (s *MCPServer) AddTool(tool *mcp.Tool, toolHandler ToolHandler) {
	s.Server.AddTool(tool, toolHandler)
	s.rwLock.Lock()
	defer s.rwLock.Unlock()
	s.tools[tool.Name] = struct{}{}
}

// RemoveTool removes a tool from the server
func (s *MCPServer) RemoveTool(toolName string) {
	s.Server.RemoveTools(toolName)
	s.rwLock.Lock()
	defer s.rwLock.Unlock()
	delete(s.tools, toolName)
}

// AddPrompt adds a prompt to the server
func (s *MCPServer) AddPrompt(prompt *mcp.Prompt, promptHandler PromptHandler) {
	s.Server.AddPrompt(prompt, promptHandler)
	s.rwLock.Lock()
	defer s.rwLock.Unlock()
	s.prompts[prompt.Name] = struct{}{}
}

// RemovePrompt removes a prompt from the server
func (s *MCPServer) RemovePrompt(promptName string) {
	s.Server.RemovePrompts(promptName)
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

// GetServer returns the underlying mcp.Server for middleware registration
func (s *MCPServer) GetServer() *mcp.Server {
	return s.Server
}
