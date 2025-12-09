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
	"sync"

	"github.com/ThinkInAIXYZ/go-mcp/protocol"
	"github.com/ThinkInAIXYZ/go-mcp/server"
	"github.com/ThinkInAIXYZ/go-mcp/transport"

	"mcp_proxy/pkg/util"
)

// MCPServer ...
type MCPServer struct {
	Server                *server.Server
	Transport             transport.ServerTransport
	SSEHandler            *transport.SSEHandler
	StreamableHTTPHandler *transport.StreamableHTTPHandler
	name                  string
	tools                 map[string]struct{}
	prompts               map[string]struct{}
	rwLock                *sync.RWMutex
}

// NewMCPServer ...
func NewMCPServer(transport transport.ServerTransport, handler *transport.SSEHandler,
	streamableHTTPHandler *transport.StreamableHTTPHandler, name string,
) *MCPServer {
	mcpServer, err := server.NewServer(transport)
	if err != nil {
		panic(err)
	}
	return &MCPServer{
		Server:                mcpServer,
		Transport:             transport,
		SSEHandler:            handler,
		StreamableHTTPHandler: streamableHTTPHandler,
		tools:                 make(map[string]struct{}),
		prompts:               make(map[string]struct{}),
		rwLock:                &sync.RWMutex{},
		name:                  name,
	}
}

// IsRegisteredTool checks if the tool is registered
func (s *MCPServer) IsRegisteredTool(toolName string) bool {
	s.rwLock.RLock()
	defer s.rwLock.RUnlock()
	_, ok := s.tools[toolName]
	return ok
}

// IsRegisteredPrompt checks if the prompt is registered
func (s *MCPServer) IsRegisteredPrompt(promptName string) bool {
	s.rwLock.RLock()
	defer s.rwLock.RUnlock()
	_, ok := s.prompts[promptName]
	return ok
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

// GetPrompts ...
func (s *MCPServer) GetPrompts() []string {
	s.rwLock.RLock()
	defer s.rwLock.RUnlock()
	promptNames := make([]string, 0, len(s.prompts))
	for promptName := range s.prompts {
		promptNames = append(promptNames, promptName)
	}
	return promptNames
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

// UnregisterTool unregisterTool unregisters a tool from the server
func (s *MCPServer) UnregisterTool(toolName string) {
	s.Server.UnregisterTool(toolName)
	s.rwLock.Lock()
	defer s.rwLock.Unlock()
	delete(s.tools, toolName)
}

// RegisterPrompt ...
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

// RegisterResources ...
func (s *MCPServer) RegisterResources(resource *protocol.Resource, resourceHandler server.ResourceHandlerFunc) {
	s.Server.RegisterResource(resource, resourceHandler)
}
