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
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestNewMCPProxy(t *testing.T) {
	messageUrlFormat := "/api/mcp/%s/message"
	proxy := NewMCPProxy(messageUrlFormat)

	assert.NotNil(t, proxy)
	assert.NotNil(t, proxy.mcpServers)
	assert.NotNil(t, proxy.rwLock)
	assert.NotNil(t, proxy.activeMCPServers)
	assert.Equal(t, messageUrlFormat, proxy.messageUrlFormat)
	assert.Empty(t, proxy.mcpServers)
	assert.Empty(t, proxy.activeMCPServers)
}

func TestMCPProxy_IsMCPServerExist(t *testing.T) {
	proxy := NewMCPProxy("/api/mcp/%s/message")

	// Test non-existent server
	assert.False(t, proxy.IsMCPServerExist("test-server"))

	// Add a mock server entry manually
	proxy.rwLock.Lock()
	proxy.mcpServers["test-server"] = &MCPServer{}
	proxy.rwLock.Unlock()

	// Test existent server
	assert.True(t, proxy.IsMCPServerExist("test-server"))
}

func TestMCPProxy_GetMCPServer(t *testing.T) {
	proxy := NewMCPProxy("/api/mcp/%s/message")

	// Test non-existent server
	assert.Nil(t, proxy.GetMCPServer("test-server"))

	// Add a mock server entry manually
	mockServer := &MCPServer{name: "test-server"}
	proxy.rwLock.Lock()
	proxy.mcpServers["test-server"] = mockServer
	proxy.rwLock.Unlock()

	// Test existent server
	result := proxy.GetMCPServer("test-server")
	assert.NotNil(t, result)
	assert.Equal(t, "test-server", result.name)
}

func TestMCPProxy_AddMCPServer(t *testing.T) {
	proxy := NewMCPProxy("/api/mcp/%s/message")

	mockServer := &MCPServer{name: "test-server"}
	proxy.AddMCPServer("test-server", mockServer)

	assert.True(t, proxy.IsMCPServerExist("test-server"))
	assert.Equal(t, mockServer, proxy.GetMCPServer("test-server"))
}

func TestMCPProxy_GetActiveMCPServerNames(t *testing.T) {
	proxy := NewMCPProxy("/api/mcp/%s/message")

	// Initially empty
	names := proxy.GetActiveMCPServerNames()
	assert.Empty(t, names)

	// Add active servers manually
	proxy.rwLock.Lock()
	proxy.activeMCPServers["server1"] = struct{}{}
	proxy.activeMCPServers["server2"] = struct{}{}
	proxy.rwLock.Unlock()

	names = proxy.GetActiveMCPServerNames()
	assert.Len(t, names, 2)
	assert.Contains(t, names, "server1")
	assert.Contains(t, names, "server2")
}

func TestMCPProxy_DeleteMCPServer(t *testing.T) {
	proxy := NewMCPProxy("/api/mcp/%s/message")

	// Test deleting non-existent server (should not panic)
	proxy.DeleteMCPServer("non-existent")

	// Add a mock server
	proxy.rwLock.Lock()
	proxy.mcpServers["test-server"] = &MCPServer{name: "test-server"}
	proxy.activeMCPServers["test-server"] = struct{}{}
	proxy.rwLock.Unlock()

	assert.True(t, proxy.IsMCPServerExist("test-server"))

	// Note: DeleteMCPServer calls Shutdown which requires a valid Server
	// So we only test the basic logic here without actual server
}

func TestMCPProxy_Run(t *testing.T) {
	proxy := NewMCPProxy("/api/mcp/%s/message")

	ctx := context.Background()

	// Run with no servers should not panic
	proxy.Run(ctx)
	assert.Empty(t, proxy.GetActiveMCPServerNames())
}
