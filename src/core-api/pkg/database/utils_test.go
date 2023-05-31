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

package database

import (
	. "github.com/onsi/ginkgo/v2"
	"github.com/stretchr/testify/assert"
)

var _ = Describe("Utils", func() {
	Describe("truncateArgs", func() {
		Context("a string", func() {
			var a string
			BeforeEach(func() {
				a = `abc`
			})
			It("less than", func() {
				b := truncateArgs(a, 10)
				assert.Equal(GinkgoT(), `"abc"`, b)
			})
			It("just equals", func() {
				b := truncateArgs(a, 5)
				assert.Equal(GinkgoT(), `"abc"`, b)
			})
			It("greater than", func() {
				b := truncateArgs(a, 2)
				assert.Equal(GinkgoT(), `"a`, b)
			})
		})

		Context("a interface", func() {
			var a []int64
			BeforeEach(func() {
				a = []int64{1, 2, 3, 4, 5, 6}
			})
			It("less than", func() {
				b := truncateArgs(a, 20)
				assert.Equal(GinkgoT(), `[1,2,3,4,5,6]`, b)
			})
			It("just equals", func() {
				b := truncateArgs(a, 22)
				assert.Equal(GinkgoT(), `[1,2,3,4,5,6]`, b)
			})
			It("greater than", func() {
				b := truncateArgs(a, 2)
				assert.Equal(GinkgoT(), `[1`, b)
			})
		})
	})
})
