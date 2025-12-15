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

package cacheimpls

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func TestNewRandomDuration(t *testing.T) {
	randomFunc := newRandomDuration(30)

	// Call multiple times to ensure it returns different values
	durations := make(map[time.Duration]bool)
	for i := 0; i < 100; i++ {
		d := randomFunc()
		durations[d] = true

		// Ensure duration is within expected range (0 to 30 seconds)
		assert.GreaterOrEqual(t, d, time.Duration(0))
		assert.Less(t, d, 30*time.Second)
	}

	// Should have some variation (not all the same)
	assert.Greater(t, len(durations), 1)
}

func TestNewRandomDuration_DifferentSeconds(t *testing.T) {
	tests := []struct {
		name    string
		seconds int
		maxMs   int64
	}{
		{
			name:    "10 seconds",
			seconds: 10,
			maxMs:   10000,
		},
		{
			name:    "60 seconds",
			seconds: 60,
			maxMs:   60000,
		},
		{
			name:    "1 second",
			seconds: 1,
			maxMs:   1000,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			randomFunc := newRandomDuration(tt.seconds)

			for i := 0; i < 50; i++ {
				d := randomFunc()
				assert.GreaterOrEqual(t, d.Milliseconds(), int64(0))
				assert.Less(t, d.Milliseconds(), tt.maxMs)
			}
		})
	}
}

func TestCacheVariables_NotNil(t *testing.T) {
	assert.NotNil(t, gatewayIDCache)
	assert.NotNil(t, gatewayNameCache)
	assert.NotNil(t, stageCache)
	assert.NotNil(t, mcpServerCache)
	assert.NotNil(t, jwtInfoCache)
	assert.NotNil(t, appMCPServerPermission)
}
