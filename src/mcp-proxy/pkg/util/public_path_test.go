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
 * either express or implied. See the License for the specific language governing permissions
 * and limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */

package util_test

import (
	"net/http"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"mcp_proxy/pkg/util"
)

var _ = Describe("RequestWithPublicPathPrefix", func() {
	It("returns same request when prefix is empty", func() {
		req, err := http.NewRequest(http.MethodGet, "http://localhost/bk/sse", nil)
		Expect(err).NotTo(HaveOccurred())
		out := util.RequestWithPublicPathPrefix(req, "")
		Expect(out).To(BeIdenticalTo(req))
	})

	It("prepends normalized prefix", func() {
		req, err := http.NewRequest(http.MethodGet, "http://localhost/bk/sse", nil)
		Expect(err).NotTo(HaveOccurred())
		out := util.RequestWithPublicPathPrefix(req, "/api/gw/")
		Expect(out).NotTo(BeIdenticalTo(req))
		Expect(out.URL.Path).To(Equal("/api/gw/bk/sse"))
		Expect(req.URL.Path).To(Equal("/bk/sse"))
	})

	It("does not double-prefix", func() {
		req, err := http.NewRequest(http.MethodGet, "http://localhost/api/gw/bk/sse", nil)
		Expect(err).NotTo(HaveOccurred())
		out := util.RequestWithPublicPathPrefix(req, "/api/gw")
		Expect(out).To(BeIdenticalTo(req))
	})
})
