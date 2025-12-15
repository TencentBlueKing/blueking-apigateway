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

package mcp

import (
	"context"
	"testing"
	"time"

	"github.com/getkin/kin-openapi/openapi3"
	"github.com/stretchr/testify/assert"

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/infra/proxy"
)

func TestConfig_Fields(t *testing.T) {
	openapiData := &openapi3.T{
		OpenAPI: "3.0.0",
		Info: &openapi3.Info{
			Title:   "Test API",
			Version: "1.0.0",
		},
	}

	cfg := &Config{
		resourceVersion: 123,
		openapiFileData: openapiData,
	}

	assert.Equal(t, 123, cfg.resourceVersion)
	assert.NotNil(t, cfg.openapiFileData)
	assert.Equal(t, "Test API", cfg.openapiFileData.Info.Title)
	assert.Equal(t, "1.0.0", cfg.openapiFileData.Info.Version)
}

func TestMCP_Creation(t *testing.T) {
	mcpProxy := proxy.NewMCPProxy("/mcp/%s/message")

	mcp := &MCP{
		proxy: mcpProxy,
	}

	assert.NotNil(t, mcp)
	assert.NotNil(t, mcp.proxy)
}

func TestMCP_Run_ContextCancellation(t *testing.T) {
	// Setup config with short interval for testing
	config.G = &config.Config{
		McpServer: config.McpServer{
			Interval: 100 * time.Millisecond,
		},
	}

	mcpProxy := proxy.NewMCPProxy("/mcp/%s/message")
	mcp := &MCP{
		proxy: mcpProxy,
	}

	ctx, cancel := context.WithCancel(context.Background())

	// Run should return the proxy
	result := mcp.Run(ctx)
	assert.Equal(t, mcpProxy, result)

	// Cancel context to stop the goroutine
	cancel()

	// Give some time for the goroutine to stop
	time.Sleep(200 * time.Millisecond)
}

func TestMCPProxy_BasicOperations(t *testing.T) {
	mcpProxy := proxy.NewMCPProxy("/mcp/%s/message")

	// Test IsMCPServerExist for non-existent server
	assert.False(t, mcpProxy.IsMCPServerExist("non-existent"))

	// Test GetMCPServer for non-existent server
	assert.Nil(t, mcpProxy.GetMCPServer("non-existent"))

	// Test GetActiveMCPServerNames when empty
	names := mcpProxy.GetActiveMCPServerNames()
	assert.Empty(t, names)
}

func TestMCPProxy_AddMCPServerFromOpenAPISpec(t *testing.T) {
	mcpProxy := proxy.NewMCPProxy("/mcp/%s/message")

	// Create a minimal OpenAPI spec
	openapiSpec := &openapi3.T{
		OpenAPI: "3.0.0",
		Info: &openapi3.Info{
			Title:   "Test API",
			Version: "1.0.0",
		},
		Servers: []*openapi3.Server{
			{URL: "https://api.example.com"},
		},
		Paths: &openapi3.Paths{},
	}

	// Add operation to paths
	pathItem := &openapi3.PathItem{
		Get: &openapi3.Operation{
			OperationID: "getUsers",
			Summary:     "Get users",
			Responses:   &openapi3.Responses{},
		},
	}
	openapiSpec.Paths.Set("/users", pathItem)

	err := mcpProxy.AddMCPServerFromOpenAPISpec("test-server", 1, openapiSpec, []string{"getUsers"})
	assert.NoError(t, err)

	// Verify server was added
	assert.True(t, mcpProxy.IsMCPServerExist("test-server"))

	// Get the server
	server := mcpProxy.GetMCPServer("test-server")
	assert.NotNil(t, server)
	assert.Equal(t, 1, server.GetResourceVersionID())
}

func TestMCPProxy_DeleteMCPServer(t *testing.T) {
	mcpProxy := proxy.NewMCPProxy("/mcp/%s/message")

	// Create a minimal OpenAPI spec
	openapiSpec := &openapi3.T{
		OpenAPI: "3.0.0",
		Info: &openapi3.Info{
			Title:   "Test API",
			Version: "1.0.0",
		},
		Servers: []*openapi3.Server{
			{URL: "https://api.example.com"},
		},
		Paths: &openapi3.Paths{},
	}

	err := mcpProxy.AddMCPServerFromOpenAPISpec("test-server", 1, openapiSpec, []string{})
	assert.NoError(t, err)
	assert.True(t, mcpProxy.IsMCPServerExist("test-server"))

	// Delete the server
	mcpProxy.DeleteMCPServer("test-server")
	assert.False(t, mcpProxy.IsMCPServerExist("test-server"))

	// Delete non-existent server should not panic
	mcpProxy.DeleteMCPServer("non-existent")
}

func TestMCPProxy_UpdateMCPServerFromOpenApiSpec(t *testing.T) {
	mcpProxy := proxy.NewMCPProxy("/mcp/%s/message")

	// Create initial OpenAPI spec
	openapiSpec := &openapi3.T{
		OpenAPI: "3.0.0",
		Info: &openapi3.Info{
			Title:   "Test API",
			Version: "1.0.0",
		},
		Servers: []*openapi3.Server{
			{URL: "https://api.example.com"},
		},
		Paths: &openapi3.Paths{},
	}

	pathItem := &openapi3.PathItem{
		Get: &openapi3.Operation{
			OperationID: "getUsers",
			Summary:     "Get users",
			Responses:   &openapi3.Responses{},
		},
	}
	openapiSpec.Paths.Set("/users", pathItem)

	err := mcpProxy.AddMCPServerFromOpenAPISpec("test-server", 1, openapiSpec, []string{"getUsers"})
	assert.NoError(t, err)

	server := mcpProxy.GetMCPServer("test-server")
	assert.NotNil(t, server)
	assert.Equal(t, 1, server.GetResourceVersionID())

	// Update the server with new version
	newOpenapiSpec := &openapi3.T{
		OpenAPI: "3.0.0",
		Info: &openapi3.Info{
			Title:   "Test API Updated",
			Version: "2.0.0",
		},
		Servers: []*openapi3.Server{
			{URL: "https://api.example.com"},
		},
		Paths: &openapi3.Paths{},
	}

	newPathItem := &openapi3.PathItem{
		Get: &openapi3.Operation{
			OperationID: "getUsers",
			Summary:     "Get users updated",
			Responses:   &openapi3.Responses{},
		},
		Post: &openapi3.Operation{
			OperationID: "createUser",
			Summary:     "Create user",
			Responses:   &openapi3.Responses{},
		},
	}
	newOpenapiSpec.Paths.Set("/users", newPathItem)

	err = mcpProxy.UpdateMCPServerFromOpenApiSpec(
		server,
		"test-server",
		2,
		newOpenapiSpec,
		[]string{"getUsers", "createUser"},
	)
	assert.NoError(t, err)
	assert.Equal(t, 2, server.GetResourceVersionID())
}

func TestMCPServer_GetTools(t *testing.T) {
	mcpProxy := proxy.NewMCPProxy("/mcp/%s/message")

	openapiSpec := &openapi3.T{
		OpenAPI: "3.0.0",
		Info: &openapi3.Info{
			Title:   "Test API",
			Version: "1.0.0",
		},
		Servers: []*openapi3.Server{
			{URL: "https://api.example.com"},
		},
		Paths: &openapi3.Paths{},
	}

	pathItem := &openapi3.PathItem{
		Get: &openapi3.Operation{
			OperationID: "getUsers",
			Summary:     "Get users",
			Responses:   &openapi3.Responses{},
		},
	}
	openapiSpec.Paths.Set("/users", pathItem)

	err := mcpProxy.AddMCPServerFromOpenAPISpec("test-server", 1, openapiSpec, []string{"getUsers"})
	assert.NoError(t, err)

	server := mcpProxy.GetMCPServer("test-server")
	assert.NotNil(t, server)

	tools := server.GetTools()
	assert.Contains(t, tools, "getUsers")
}

func TestMCPServer_UnregisterTool(t *testing.T) {
	mcpProxy := proxy.NewMCPProxy("/mcp/%s/message")

	openapiSpec := &openapi3.T{
		OpenAPI: "3.0.0",
		Info: &openapi3.Info{
			Title:   "Test API",
			Version: "1.0.0",
		},
		Servers: []*openapi3.Server{
			{URL: "https://api.example.com"},
		},
		Paths: &openapi3.Paths{},
	}

	pathItem := &openapi3.PathItem{
		Get: &openapi3.Operation{
			OperationID: "getUsers",
			Summary:     "Get users",
			Responses:   &openapi3.Responses{},
		},
		Post: &openapi3.Operation{
			OperationID: "createUser",
			Summary:     "Create user",
			Responses:   &openapi3.Responses{},
		},
	}
	openapiSpec.Paths.Set("/users", pathItem)

	err := mcpProxy.AddMCPServerFromOpenAPISpec("test-server", 1, openapiSpec, []string{"getUsers", "createUser"})
	assert.NoError(t, err)

	server := mcpProxy.GetMCPServer("test-server")
	assert.NotNil(t, server)

	tools := server.GetTools()
	assert.Contains(t, tools, "getUsers")
	assert.Contains(t, tools, "createUser")

	// Unregister a tool
	server.UnregisterTool("createUser")

	tools = server.GetTools()
	assert.Contains(t, tools, "getUsers")
	assert.NotContains(t, tools, "createUser")
}
