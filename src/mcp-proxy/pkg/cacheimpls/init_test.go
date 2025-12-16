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

package cacheimpls_test

import (
	"time"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"mcp_proxy/pkg/cacheimpls"
)

var _ = Describe("Init", func() {
	Describe("NewRandomDuration", func() {
		It("should return random durations within expected range", func() {
			randomFunc := cacheimpls.NewRandomDuration(30)

			durations := make(map[time.Duration]bool)
			for i := 0; i < 100; i++ {
				d := randomFunc()
				durations[d] = true

				Expect(d).To(BeNumerically(">=", time.Duration(0)))
				Expect(d).To(BeNumerically("<", 30*time.Second))
			}

			// Should have some variation
			Expect(len(durations)).To(BeNumerically(">", 1))
		})

		DescribeTable("handles different seconds values",
			func(seconds int, maxMs int64) {
				randomFunc := cacheimpls.NewRandomDuration(seconds)

				for i := 0; i < 50; i++ {
					d := randomFunc()
					Expect(d.Milliseconds()).To(BeNumerically(">=", int64(0)))
					Expect(d.Milliseconds()).To(BeNumerically("<", maxMs))
				}
			},
			Entry("10 seconds", 10, int64(10000)),
			Entry("60 seconds", 60, int64(60000)),
			Entry("1 second", 1, int64(1000)),
		)
	})

	Describe("Cache Variables", func() {
		It("should have initialized cache variables", func() {
			Expect(cacheimpls.GetGatewayIDCache()).NotTo(BeNil())
			Expect(cacheimpls.GetGatewayNameCache()).NotTo(BeNil())
			Expect(cacheimpls.GetStageCache()).NotTo(BeNil())
			Expect(cacheimpls.GetMCPServerCache()).NotTo(BeNil())
			Expect(cacheimpls.GetJWTInfoCache()).NotTo(BeNil())
			Expect(cacheimpls.GetAppMCPServerPermission()).NotTo(BeNil())
		})
	})
})
