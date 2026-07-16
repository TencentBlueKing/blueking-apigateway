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

// Package runner ...
package runner

import (
	"context"
	"fmt"
	"os"

	"github.com/prometheus/client_golang/prometheus"
	clientv3 "go.etcd.io/etcd/client/v3"
	"go.uber.org/zap"

	"operator/pkg/config"
	"operator/pkg/core/agent"
	"operator/pkg/core/agent/timer"
	"operator/pkg/core/committer"
	"operator/pkg/core/registry"
	"operator/pkg/core/store"
	"operator/pkg/core/synchronizer"
	"operator/pkg/leaderelection"
	"operator/pkg/logging"
	"operator/pkg/metric"
	"operator/pkg/server"
)

// EtcdAgentRunner ...
type EtcdAgentRunner struct {
	client            *clientv3.Client
	apigwEtcdRegistry *registry.APIGWEtcdRegistry
	leader            *leaderelection.EtcdLeaderElector
	synchronizer      *synchronizer.ApisixConfigSynchronizer
	apisixEtcdstore   *store.ApisixEtcdStore

	committer *committer.Committer
	agent     *agent.EventAgent

	cfg *config.Config

	logger *zap.SugaredLogger

	// ctx for managing the lifecycle of background goroutines
	ctx    context.Context
	cancel context.CancelFunc
}

// NewEtcdAgentRunner ...
func NewEtcdAgentRunner(ctx context.Context, cfg *config.Config) *EtcdAgentRunner {
	client, err := initOperatorEtcdClient(cfg)
	if err != nil {
		fmt.Println(err, "Error creating apigwEtcdRegistry etcd client")
		os.Exit(1)
	}

	// Create a cancellable context for managing background goroutines
	runnerCtx, cancel := context.WithCancel(ctx)

	r := &EtcdAgentRunner{
		client: client,
		cfg:    cfg,
		logger: logging.GetLogger().Named("etcd-agent-runner"),
		ctx:    runnerCtx,
		cancel: cancel,
	}
	r.init()
	return r
}

func (r *EtcdAgentRunner) init() {
	// 1. init metrics
	metric.InitMetric(prometheus.DefaultRegisterer)

	// 2. init apigwEtcdRegistry
	r.apigwEtcdRegistry = registry.NewAPIGWEtcdRegistry(
		r.client,
		r.cfg.Dashboard.Etcd.KeyPrefix,
		r.cfg.Operator.WatchEventChanSize,
	)

	r.leader, _ = leaderelection.NewEtcdLeaderElector(r.client, r.cfg.Dashboard.Etcd.KeyPrefix)
	// 4. init output
	apisixEtcdStore, err := initApisixEtcdStore(r.ctx, r.cfg)
	if err != nil {
		fmt.Println(err, "Error creating etcd apisixEtcdstore")
		os.Exit(1)
	}
	r.apisixEtcdstore = apisixEtcdStore
	r.synchronizer = synchronizer.NewSynchronizer(
		apisixEtcdStore,
		"/healthz",
		r.cfg.Operator.GatewaySyncConcurrency,
	)

	stageTimer := timer.NewReleaseTimer()
	// 5. init committer
	r.committer = committer.NewCommitter(
		r.apigwEtcdRegistry,
		r.synchronizer,
		stageTimer,
		r.cfg.Operator.CommitResourceChanSize,
	)
	commitChan := r.committer.GetCommitChan()

	// 6. init agent
	r.agent = agent.NewEventAgent(
		r.apigwEtcdRegistry,
		commitChan,
		r.synchronizer,
		stageTimer,
	)
}

// Close releases all resources and stops background goroutines
func (r *EtcdAgentRunner) Close() {
	if r.cancel != nil {
		r.cancel()
	}
	if r.apisixEtcdstore != nil {
		r.apisixEtcdstore.Close()
	}
	r.logger.Info("EtcdAgentRunner closed")
}

// Run ...
func (r *EtcdAgentRunner) Run(ctx context.Context) {
	// 1. run http server
	httpServer := server.NewServer(
		r.leader,
		r.apigwEtcdRegistry,
		r.apisixEtcdstore,
		r.committer,
	)
	httpServer.RegisterMetric(prometheus.DefaultGatherer)
	if err := httpServer.Run(ctx, r.cfg); err != nil {
		r.logger.Errorw("http server run failed", "err", err)
	}

	// 2. waiting leader election
	var keepAliveChan <-chan struct{} = make(chan struct{})
	if r.leader != nil {
		r.leader.Run(ctx)
		r.logger.Info("waiting for becoming leader...")
		keepAliveChan = r.leader.WaitForLeading()
	}

	// 3. run committer
	r.logger.Info("starting committer")
	go r.committer.Run(ctx)

	// 4. run agent
	r.agent.SetKeepAliveChan(keepAliveChan)

	r.logger.Info("starting etcd agent")
	r.agent.Run(ctx)
	r.logger.Error("Agent stopped running")
}
