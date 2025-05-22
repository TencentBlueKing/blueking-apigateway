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
	"sync"

	"github.com/ThinkInAIXYZ/go-mcp/protocol"
	"github.com/ThinkInAIXYZ/go-mcp/server"
	"github.com/ThinkInAIXYZ/go-mcp/transport"

	"mcp_proxy/pkg/util"
)

type McpServer struct {
	Server    *server.Server
	Transport transport.ServerTransport
	Handler   *transport.SSEHandler
	version   string
	name      string
	tools     map[string]struct{}
	rwLock    *sync.RWMutex
}

func NewMcpServer(transport transport.ServerTransport,
	handler *transport.SSEHandler,
	name string,
) *McpServer {
	mcpServer, err := server.NewServer(transport)
	if err != nil {
		panic(err)
	}
	return &McpServer{
		Server:    mcpServer,
		Transport: transport,
		Handler:   handler,
		tools:     make(map[string]struct{}),
		rwLock:    &sync.RWMutex{},
		name:      name,
	}
}

// IsRegisteredTool checks if the tool is registered
func (s *McpServer) IsRegisteredTool(toolName string) bool {
	s.rwLock.RLock()
	defer s.rwLock.RUnlock()
	_, ok := s.tools[toolName]
	return ok
}

func (s *McpServer) GetTools() []string {
	s.rwLock.RLock()
	defer s.rwLock.RUnlock()
	toolNames := make([]string, 0, len(s.tools))
	for toolName := range s.tools {
		toolNames = append(toolNames, toolName)
	}
	return toolNames
}

func (s *McpServer) Run(ctx context.Context) {
	util.GoroutineWithRecovery(ctx, func() {
		if err := s.Server.Run(); err != nil {
			panic(err)
		}
	})
}

func (s *McpServer) Shutdown(ctx context.Context) {
	util.GoroutineWithRecovery(ctx, func() {
		if err := s.Server.Shutdown(ctx); err != nil {
			panic(err)
		}
	})
}

func (s *McpServer) RegisterTool(tool *protocol.Tool, toolHandler server.ToolHandlerFunc) {
	s.Server.RegisterTool(tool, toolHandler)
	s.rwLock.Lock()
	defer s.rwLock.Unlock()
	s.tools[tool.Name] = struct{}{}
}

// UnregisterTool unregisterTool unregisters a tool from the server
func (s *McpServer) UnregisterTool(toolName string) {
	s.Server.UnregisterTool(toolName)
	s.rwLock.Lock()
	defer s.rwLock.Unlock()
	delete(s.tools, toolName)
}

func (s *McpServer) RegisterResources(resource *protocol.Resource, resourceHandler server.ResourceHandlerFunc) {
	s.Server.RegisterResource(resource, resourceHandler)
}
