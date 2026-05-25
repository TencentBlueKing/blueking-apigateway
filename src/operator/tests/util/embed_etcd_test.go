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
	"os"
	"testing"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	clientv3 "go.etcd.io/etcd/client/v3"
	"go.etcd.io/etcd/server/v3/embed"

	"operator/tests/util"
)

func TestMockEtcd(t *testing.T) {
	RegisterFailHandler(Fail)
	RunSpecs(t, "Integration Suite")
}

var _ = Describe("EmbeddedEtcd", func() {
	var (
		etcd   *embed.Etcd
		err    error
		client *clientv3.Client
	)

	BeforeEach(func() {
		// Start the embedded etcd server
		client, etcd, err = util.StartEmbedEtcdClient(context.Background())
		Expect(err).ShouldNot(HaveOccurred())
	})

	AfterEach(func() {
		// Close the client connection.
		client.Close()

		// Shutdown the embedded etcd server.
		etcd.Close()
		// Remove the etcd data directory
		_ = os.RemoveAll(etcd.Config().Dir)
	})

	It("should be able to put and get a key", func() {
		key := "test_key"
		value := "test_value"

		// Put a key-value pair into the etcd server.
		_, err = client.Put(context.Background(), key, value)
		Expect(err).ShouldNot(HaveOccurred())

		// Get the key-value pair from the etcd server.
		resp, err := client.Get(context.Background(), key)
		Expect(err).ShouldNot(HaveOccurred())
		Expect(resp.Kvs).Should(HaveLen(1))
		Expect(string(resp.Kvs[0].Key)).Should(Equal(key))
		Expect(string(resp.Kvs[0].Value)).Should(Equal(value))
	})
})
