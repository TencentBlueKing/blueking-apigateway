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

package util

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestGenUUID4(t *testing.T) {
	uuid := GenUUID4()

	// UUID4 hex encoded is 32 characters (16 bytes * 2)
	assert.Len(t, uuid, 32)

	// Should be valid hex
	for _, c := range uuid {
		assert.True(t, (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'),
			"UUID should only contain hex characters")
	}
}

func TestGenUUID4_Uniqueness(t *testing.T) {
	uuids := make(map[string]bool)

	// Generate 100 UUIDs and check uniqueness
	for i := 0; i < 100; i++ {
		uuid := GenUUID4()
		assert.False(t, uuids[uuid], "UUID should be unique")
		uuids[uuid] = true
	}
}

func TestGenUUID4_NotEmpty(t *testing.T) {
	uuid := GenUUID4()
	assert.NotEmpty(t, uuid)
}
