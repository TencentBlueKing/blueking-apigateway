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

package util_test

import (
	. "github.com/onsi/ginkgo/v2"
	"github.com/stretchr/testify/assert"

	"core/pkg/util"
)

var _ = Describe("String", func() {
	Describe("TruncateBytes", func() {
		s := []byte("helloworld")

		DescribeTable("TruncateBytes cases", func(expected []byte, truncatedSize int) {
			assert.Equal(GinkgoT(), expected, util.TruncateBytes(s, truncatedSize))
		},
			Entry("truncated size less than real size", []byte("he"), 2),
			Entry("truncated size equals to real size", s, 10),
			Entry("truncated size greater than real size", s, 20),
		)
	})

	Describe("TruncateBytesToString", func() {
		s := []byte("helloworld")
		sStr := string(s)

		DescribeTable("TruncateBytesToString cases", func(expected string, truncatedSize int) {
			assert.Equal(GinkgoT(), expected, util.TruncateBytesToString(s, truncatedSize))
		},
			Entry("truncated size less than real size", "he", 2),
			Entry("truncated size equals to real size", sStr, 10),
			Entry("truncated size greater than real size", sStr, 20),
		)
	})
})
