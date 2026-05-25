// Package metric ...
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

// Package metric ...
package metric

import (
	"github.com/prometheus/client_golang/prometheus"
)

// ResultSuccess ...
const (
	ResultSuccess = "succ"
	ResultFail    = "fail"
	ActionGet     = "get"
	ActionPut     = "put"
	ActionList    = "list"
	ActionWatch   = "watch"
	ActionUpdate  = "update"
	ActionDelete  = "delete"
	ActionCreate  = "create"
)

// BootstrapSyncingCounter ...
var (
	LeaderElectionGauge           *prometheus.GaugeVec
	ResourceEventTriggeredCounter *prometheus.CounterVec
	ResourceConvertedCounter      *prometheus.CounterVec
	SyncCmpCounter                *prometheus.CounterVec
	SyncCmpDiffCounter            *prometheus.CounterVec
	SynchronizerEventCounter      *prometheus.CounterVec
	SynchronizerFlushingCounter   *prometheus.CounterVec
	SynchronizerFlushingHistogram *prometheus.HistogramVec
	ApisixResourceWrittenCounter  *prometheus.CounterVec
	ApisixOperationCounter        *prometheus.CounterVec
	ApisixOperationHistogram      *prometheus.HistogramVec
	RegistryActionCounter         *prometheus.CounterVec
	RegistryActionHistogram       *prometheus.HistogramVec
)

// InitMetric ...
func InitMetric(register prometheus.Registerer) {
	LeaderElectionGauge = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "leader_election_info",
			Help: "leader_election describe whether agent is leader",
		},
		[]string{"hostname"},
	)
	ResourceEventTriggeredCounter = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "resource_event_triggered_count",
			Help: "resource_event_triggered_count describe count of resource event",
		},
		[]string{"gateway", "stage", "type"},
	)
	ResourceConvertedCounter = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "resource_converted_count",
			Help: "resource_converted_count describe count of resource converted",
		},
		[]string{"gateway", "stage", "type"},
	)

	SyncCmpCounter = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "sync_cmp_count",
			Help: "sync_cmp_count describe count of compare",
		},
		[]string{"gateway", "stage", "type"},
	)

	SyncCmpDiffCounter = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "sync_cmp_diff_count",
			Help: "sync_cmp_diff_count describe count of compare diff",
		},
		[]string{"gateway", "stage", "type"},
	)

	SynchronizerEventCounter = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "synchronizer_event_count",
			Help: "synchronizer_event_count describe count of synchronizer event count",
		},
		[]string{"gateway", "stage"},
	)
	SynchronizerFlushingCounter = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "synchronizer_flushing_count",
			Help: "synchronizer_flushing_count describe counts of flushing process",
		},
		[]string{"gateway", "stage", "result"},
	)
	SynchronizerFlushingHistogram = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "synchronizer_flushing_histogram",
			Help:    "synchronizer_flushing_histogram describe time consuming distribution of flushing process",
			Buckets: prometheus.ExponentialBuckets(1, 2, 14),
		},
		[]string{"gateway", "stage", "result"},
	)
	ApisixResourceWrittenCounter = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "apisix_resource_written_count",
			Help: "apisix_resource_written_count describe count of apisix resource written",
		},
		[]string{"gateway", "stage", "type"},
	)
	ApisixOperationCounter = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "apisix_operation_count",
			Help: "apisix_operation_count describe counts of apisix operation",
		},
		[]string{"type", "action", "result"},
	)
	ApisixOperationHistogram = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "apisix_operation_histogram",
			Help:    "apisix_operation_histogram describe time consuming distribution of apisix operation",
			Buckets: prometheus.ExponentialBuckets(1, 2, 12),
		},
		[]string{"type", "action", "result"},
	)
	RegistryActionCounter = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "registry_action_count",
			Help: "registry_action_count describe counts of registry actions",
		},
		[]string{"type", "action", "result"},
	)
	RegistryActionHistogram = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "registry_action_histogram",
			Help:    "registry_action_histogram describe time consuming distribution of registry actions",
			Buckets: prometheus.ExponentialBuckets(1, 2, 12),
		},
		[]string{"type", "action", "result"},
	)

	register.MustRegister(LeaderElectionGauge)
	register.MustRegister(ResourceEventTriggeredCounter)
	register.MustRegister(ResourceConvertedCounter)
	register.MustRegister(SynchronizerEventCounter)
	register.MustRegister(SynchronizerFlushingCounter)
	register.MustRegister(SynchronizerFlushingHistogram)
	register.MustRegister(ApisixResourceWrittenCounter)
	register.MustRegister(ApisixOperationCounter)
	register.MustRegister(ApisixOperationHistogram)
	register.MustRegister(RegistryActionCounter)
	register.MustRegister(RegistryActionHistogram)
	register.MustRegister(SyncCmpCounter)
	register.MustRegister(SyncCmpDiffCounter)
}
