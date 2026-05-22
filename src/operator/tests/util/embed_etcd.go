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

// Package util ...
package util

import (
	"context"
	"fmt"
	"net/url"
	"os"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
	"go.etcd.io/etcd/server/v3/embed"
)

// StartEmbedEtcdClient StartEmbedEtcd starts an embedded etcd server
func StartEmbedEtcdClient(_ context.Context) (*clientv3.Client, *embed.Etcd, error) {
	cfg := embed.NewConfig()
	cfg.Dir, _ = os.MkdirTemp("", "etcd")
	cfg.LogLevel = "error"
	cfg.ListenClientUrls = []url.URL{{Scheme: "http", Host: "localhost:1234"}}
	cfg.ListenPeerUrls = []url.URL{{Scheme: "http", Host: "localhost:2345"}}

	etcd, err := embed.StartEtcd(cfg)
	if err != nil {
		return nil, nil, err
	}
	// Wait for etcd server to be ready.
	select {
	case <-etcd.Server.ReadyNotify():
		client, err := clientv3.New(clientv3.Config{
			Endpoints:   []string{etcd.Clients[0].Addr().String()},
			DialTimeout: time.Second,
		})
		return client, etcd, err
	case <-time.After(30 * time.Second):
		return nil, etcd, fmt.Errorf("embeddedEtcd server took too long to start")
	}
}
