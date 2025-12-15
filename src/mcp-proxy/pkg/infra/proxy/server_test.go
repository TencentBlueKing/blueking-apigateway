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
	"sync"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestMCPServer_IsRegisteredTool(t *testing.T) {
	server := &MCPServer{
		tools:  make(map[string]struct{}),
		rwLock: &sync.RWMutex{},
	}

	// Test non-registered tool
	assert.False(t, server.IsRegisteredTool("test-tool"))

	// Register a tool manually
	server.rwLock.Lock()
	server.tools["test-tool"] = struct{}{}
	server.rwLock.Unlock()

	// Test registered tool
	assert.True(t, server.IsRegisteredTool("test-tool"))
}

func TestMCPServer_GetResourceVersionID(t *testing.T) {
	server := &MCPServer{
		resourceVersionID: 123,
		rwLock:            &sync.RWMutex{},
	}

	assert.Equal(t, 123, server.GetResourceVersionID())
}

func TestMCPServer_SetResourceVersionID(t *testing.T) {
	server := &MCPServer{
		resourceVersionID: 123,
		rwLock:            &sync.RWMutex{},
	}

	server.SetResourceVersionID(456)
	assert.Equal(t, 456, server.GetResourceVersionID())
}

func TestMCPServer_GetTools(t *testing.T) {
	server := &MCPServer{
		tools:  make(map[string]struct{}),
		rwLock: &sync.RWMutex{},
	}

	// Initially empty
	tools := server.GetTools()
	assert.Empty(t, tools)

	// Add tools manually
	server.rwLock.Lock()
	server.tools["tool1"] = struct{}{}
	server.tools["tool2"] = struct{}{}
	server.tools["tool3"] = struct{}{}
	server.rwLock.Unlock()

	tools = server.GetTools()
	assert.Len(t, tools, 3)
	assert.Contains(t, tools, "tool1")
	assert.Contains(t, tools, "tool2")
	assert.Contains(t, tools, "tool3")
}

func TestMCPServer_ConcurrentAccess(t *testing.T) {
	server := &MCPServer{
		tools:             make(map[string]struct{}),
		rwLock:            &sync.RWMutex{},
		resourceVersionID: 0,
	}

	// Test concurrent reads and writes
	var wg sync.WaitGroup
	for i := 0; i < 100; i++ {
		wg.Add(2)
		go func() {
			defer wg.Done()
			server.GetResourceVersionID()
			server.GetTools()
			server.IsRegisteredTool("test")
		}()
		go func(version int) {
			defer wg.Done()
			server.SetResourceVersionID(version)
		}(i)
	}
	wg.Wait()
}
