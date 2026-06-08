/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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

package leaderelection_test

import (
	"context"
	"time"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"github.com/prometheus/client_golang/prometheus"
	clientv3 "go.etcd.io/etcd/client/v3"
	"go.etcd.io/etcd/server/v3/embed"

	"operator/pkg/config"
	"operator/pkg/leaderelection"
	"operator/pkg/metric"
	"operator/tests/util"
)

var (
	etcdClient *clientv3.Client
	etcdServer *embed.Etcd
)

var _ = BeforeSuite(func() {
	// 初始化 metric
	metric.InitMetric(prometheus.DefaultRegisterer)

	ctx := context.Background()
	// 使用 etcd mock 客户端
	var err error
	etcdClient, etcdServer, err = util.StartEmbedEtcdClient(ctx)
	Expect(err).To(BeNil())
	Expect(etcdClient).NotTo(BeNil())
})

var _ = AfterSuite(func() {
	if etcdClient != nil {
		etcdClient.Close()
	}
	if etcdServer != nil {
		etcdServer.Close()
	}
})

var _ = Describe("EtcdLeaderElector", func() {
	var (
		elector1 *leaderelection.EtcdLeaderElector
		elector2 *leaderelection.EtcdLeaderElector
		err      error
	)

	BeforeEach(func() {
		config.InstanceName = "test-instance1"
		config.InstanceIP = "127.0.0.1"
		elector1, err = leaderelection.NewEtcdLeaderElector(etcdClient, "test-prefix")
		Expect(err).To(BeNil())
		config.InstanceName = "test-instance2"
		config.InstanceIP = "127.0.0.2"
		elector2, err = leaderelection.NewEtcdLeaderElector(etcdClient, "test-prefix")
		Expect(err).To(BeNil())
	})

	Describe("NewEtcdLeaderElector", func() {
		It("should create a new EtcdLeaderElector without error", func() {
			Expect(elector1).NotTo(BeNil())
			Expect(elector2).NotTo(BeNil())
		})
	})

	Describe("Run", func() {
		It("should run the election process", func() {
			ctx1, cancel1 := context.WithCancel(context.Background())
			ctx2, cancel2 := context.WithCancel(context.Background())
			defer cancel1()
			defer cancel2()

			go elector1.Run(ctx1)
			go elector2.Run(ctx2)

			// 等待选举完成
			Eventually(func() string {
				return elector1.Leader()
			}, 10*time.Second, 100*time.Millisecond).ShouldNot(BeEmpty())

			// 两个选举器应该看到同一个 leader
			leader1 := elector1.Leader()
			leader2 := elector2.Leader()
			Expect(leader1).NotTo(BeEmpty())
			Expect(leader2).NotTo(BeEmpty())
			Expect(leader1).To(Equal(leader2))
		})
	})
})
