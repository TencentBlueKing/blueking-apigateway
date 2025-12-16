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

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
)

var _ = Describe("MCPServer", func() {
	Describe("IsRegisteredTool", func() {
		var server *MCPServer

		BeforeEach(func() {
			server = &MCPServer{
				tools:  make(map[string]struct{}),
				rwLock: &sync.RWMutex{},
			}
		})

		It("should return false for non-registered tool", func() {
			Expect(server.IsRegisteredTool("test-tool")).To(BeFalse())
		})

		It("should return true for registered tool", func() {
			server.rwLock.Lock()
			server.tools["test-tool"] = struct{}{}
			server.rwLock.Unlock()

			Expect(server.IsRegisteredTool("test-tool")).To(BeTrue())
		})
	})

	Describe("GetResourceVersionID", func() {
		It("should return the resource version ID", func() {
			server := &MCPServer{
				resourceVersionID: 123,
				rwLock:            &sync.RWMutex{},
			}

			Expect(server.GetResourceVersionID()).To(Equal(123))
		})
	})

	Describe("SetResourceVersionID", func() {
		It("should set the resource version ID", func() {
			server := &MCPServer{
				resourceVersionID: 123,
				rwLock:            &sync.RWMutex{},
			}

			server.SetResourceVersionID(456)
			Expect(server.GetResourceVersionID()).To(Equal(456))
		})
	})

	Describe("GetTools", func() {
		var server *MCPServer

		BeforeEach(func() {
			server = &MCPServer{
				tools:  make(map[string]struct{}),
				rwLock: &sync.RWMutex{},
			}
		})

		It("should return empty list initially", func() {
			tools := server.GetTools()
			Expect(tools).To(BeEmpty())
		})

		It("should return all registered tools", func() {
			server.rwLock.Lock()
			server.tools["tool1"] = struct{}{}
			server.tools["tool2"] = struct{}{}
			server.tools["tool3"] = struct{}{}
			server.rwLock.Unlock()

			tools := server.GetTools()
			Expect(tools).To(HaveLen(3))
			Expect(tools).To(ContainElements("tool1", "tool2", "tool3"))
		})
	})

	Describe("ConcurrentAccess", func() {
		It("should handle concurrent reads and writes", func() {
			server := &MCPServer{
				tools:             make(map[string]struct{}),
				rwLock:            &sync.RWMutex{},
				resourceVersionID: 0,
			}

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
		})
	})
})
