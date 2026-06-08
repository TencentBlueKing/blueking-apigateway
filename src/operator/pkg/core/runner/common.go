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
	"strings"

	clientv3 "go.etcd.io/etcd/client/v3"
	"google.golang.org/grpc"

	"operator/pkg/config"
	"operator/pkg/core/store"
	"operator/pkg/logging"
	"operator/pkg/utils"
)

func initApisixEtcdStore(ctx context.Context, cfg *config.Config) (apisixStore *store.ApisixEtcdStore, err error) {
	client, err := initApisixEtcdClient(cfg)
	if err != nil {
		return nil, fmt.Errorf("init etcd client failed: %w", err)
	}
	apisixStore, err = store.NewApisixEtcdStore(
		ctx,
		client,
		cfg.Apisix.Etcd.KeyPrefix,
		cfg.Operator.EtcdPutInterval,
		cfg.Operator.EtcdDelInterval,
		cfg.Operator.EtcdSyncTimeout,
	)
	if err != nil {
		return nil, fmt.Errorf("init etcd apisixEtcdstore failed: %w", err)
	}
	return apisixStore, nil
}

func initOperatorEtcdClient(cfg *config.Config) (*clientv3.Client, error) {
	return createEtcdClient(&cfg.Dashboard.Etcd)
}

func initApisixEtcdClient(cfg *config.Config) (*clientv3.Client, error) {
	return createEtcdClient(&cfg.Apisix.Etcd)
}

func createEtcdClient(config *config.Etcd) (*clientv3.Client, error) {
	if len(config.Endpoints) == 0 {
		fmt.Println("Etcd endpoints is empty")
		os.Exit(1)
	}
	opts := make([]grpc.DialOption, 0)
	opt := clientv3.Config{
		Endpoints:   strings.Split(config.Endpoints, ","),
		Logger:      logging.GetControllerLogger().Named("etcd"),
		DialOptions: opts,
	}
	if !config.WithoutAuth {
		cafile := config.CACert
		certfile := config.Cert
		keyfile := config.Key
		if cafile != "" && certfile != "" && keyfile != "" {
			var err error
			opt.TLS, err = utils.NewClientTLSConfig(cafile, certfile, keyfile)
			if err != nil {
				fmt.Println(err, "Create Etcd tls config failed")
				os.Exit(1)
			}
		}
		username := config.Username
		password := config.Password
		if username != "" && password != "" {
			opt.Username = username
			opt.Password = password
		}
	}
	return clientv3.New(opt)
}
