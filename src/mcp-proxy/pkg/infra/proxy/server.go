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
)

// MCPServer ...
type MCPServer struct {
	Server  *mcp.Server
	Handler *mcp.SSEHandler
	name    string
	// 生效的资源版本号
	resourceVersionID int
	tools             map[string]struct{}
	prompts           map[string]struct{}
	rwLock            *sync.RWMutex
}

// NewMCPServer ...
func NewMCPServer(
	name string,
	title string,
	resourceVersion int,
) *MCPServer {
	mcpServer := mcp.NewServer(
		&mcp.Implementation{Name: name, Title: title, Version: "1.0.0"},
		nil,
	)
	return &MCPServer{
		Server:            mcpServer,
		tools:             make(map[string]struct{}),
		prompts:           make(map[string]struct{}),
		rwLock:            &sync.RWMutex{},
		name:              name,
		resourceVersionID: resourceVersion,
	}
}

// SetHandler sets the SSE handler for the server
func (s *MCPServer) SetHandler(handler *mcp.SSEHandler) {
	s.Handler = handler
}

// HandleSSE returns the http.Handler for SSE connections
func (s *MCPServer) HandleSSE() http.Handler {
	if s.Handler != nil {
		return s.Handler
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
// Note: 官方 SDK 的 Server.Run 需要传入 transport，这里改为在 proxy 层处理
func (s *MCPServer) Run(ctx context.Context) {
	// 官方 SDK 使用 SSEHandler 来处理连接，不需要单独 Run
	// Server 会在 SSEHandler 处理请求时自动管理会话
}

// Shutdown ...
func (s *MCPServer) Shutdown(ctx context.Context) {
	// 官方 SDK 的 Server 没有 Shutdown 方法
	// 会话管理由 SSEHandler 处理
}

// RegisterTool ...
func (s *MCPServer) RegisterTool(tool *mcp.Tool, toolHandler mcp.ToolHandler) {
	s.Server.AddTool(tool, toolHandler)
	s.rwLock.Lock()
	defer s.rwLock.Unlock()
	s.tools[tool.Name] = struct{}{}
}

// UnregisterTool  unregisters a tool from the server
func (s *MCPServer) UnregisterTool(toolName string) {
	s.Server.RemoveTools(toolName)
	s.rwLock.Lock()
	defer s.rwLock.Unlock()
	delete(s.tools, toolName)
}

// RegisterResources ...
func (s *MCPServer) RegisterResources(resource *mcp.Resource, resourceHandler mcp.ResourceHandler) {
	s.Server.AddResource(resource, resourceHandler)
}

// RegisterPrompt registers a prompt to the server
func (s *MCPServer) RegisterPrompt(prompt *mcp.Prompt, promptHandler mcp.PromptHandler) {
	s.Server.AddPrompt(prompt, promptHandler)
	s.rwLock.Lock()
	defer s.rwLock.Unlock()
	s.prompts[prompt.Name] = struct{}{}
}

// UnregisterPrompt unregisters a prompt from the server
func (s *MCPServer) UnregisterPrompt(promptName string) {
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
