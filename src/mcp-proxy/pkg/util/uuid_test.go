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
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"mcp_proxy/pkg/util"
)

var _ = Describe("UUID", func() {
	Describe("GenUUID4", func() {
		It("should generate 32-character hex string", func() {
			uuid := util.GenUUID4()
			Expect(uuid).To(HaveLen(32))
		})

		It("should contain only hex characters", func() {
			uuid := util.GenUUID4()
			for _, c := range uuid {
				Expect((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f')).To(BeTrue(),
					"UUID should only contain hex characters")
			}
		})

		It("should generate unique UUIDs", func() {
			uuids := make(map[string]bool)

			for i := 0; i < 100; i++ {
				uuid := util.GenUUID4()
				Expect(uuids).NotTo(HaveKey(uuid), "UUID should be unique")
				uuids[uuid] = true
			}
		})

		It("should not be empty", func() {
			uuid := util.GenUUID4()
			Expect(uuid).NotTo(BeEmpty())
		})
	})
})
