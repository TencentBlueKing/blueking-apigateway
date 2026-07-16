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

package config

import (
	"testing"

	"github.com/spf13/viper"
	"github.com/stretchr/testify/require"
)

func TestLoadGatewaySyncConcurrency(t *testing.T) {
	t.Run("default", func(t *testing.T) {
		cfg, err := Load(viper.New())
		require.NoError(t, err)
		require.Equal(t, 5, cfg.Operator.GatewaySyncConcurrency)
	})

	t.Run("override", func(t *testing.T) {
		v := viper.New()
		v.Set("operator.gatewaySyncConcurrency", 3)

		cfg, err := Load(v)
		require.NoError(t, err)
		require.Equal(t, 3, cfg.Operator.GatewaySyncConcurrency)
	})

	t.Run("non-positive override uses default", func(t *testing.T) {
		v := viper.New()
		v.Set("operator.gatewaySyncConcurrency", 0)

		cfg, err := Load(v)
		require.NoError(t, err)
		require.Equal(t, 5, cfg.Operator.GatewaySyncConcurrency)
	})
}
