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

package util_test

import (
	"context"
	"sync"
	"time"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"mcp_proxy/pkg/util"
)

var _ = Describe("Goroutinex", func() {
	Describe("GoroutineWithRecovery", func() {
		It("should execute function normally", func() {
			ctx := context.Background()
			var executed bool
			var wg sync.WaitGroup
			wg.Add(1)

			util.GoroutineWithRecovery(ctx, func() {
				executed = true
				wg.Done()
			})

			done := make(chan struct{})
			go func() {
				wg.Wait()
				close(done)
			}()

			select {
			case <-done:
				Expect(executed).To(BeTrue())
			case <-time.After(time.Second):
				Fail("Goroutine did not complete in time")
			}
		})

		It("should recover from panic", func() {
			ctx := context.Background()
			var recovered bool
			var wg sync.WaitGroup
			wg.Add(1)

			util.GoroutineWithRecovery(ctx, func() {
				defer wg.Done()
				recovered = true
				panic("test panic")
			})

			done := make(chan struct{})
			go func() {
				wg.Wait()
				close(done)
			}()

			select {
			case <-done:
				Expect(recovered).To(BeTrue())
			case <-time.After(time.Second):
				Fail("Goroutine did not complete in time")
			}
		})

		It("should handle multiple goroutines", func() {
			ctx := context.Background()
			var counter int
			var mu sync.Mutex
			var wg sync.WaitGroup

			for i := 0; i < 10; i++ {
				wg.Add(1)
				util.GoroutineWithRecovery(ctx, func() {
					defer wg.Done()
					mu.Lock()
					counter++
					mu.Unlock()
				})
			}

			done := make(chan struct{})
			go func() {
				wg.Wait()
				close(done)
			}()

			select {
			case <-done:
				Expect(counter).To(Equal(10))
			case <-time.After(2 * time.Second):
				Fail("Goroutines did not complete in time")
			}
		})
	})
})
