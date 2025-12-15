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
	"context"
	"sync"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func TestGoroutineWithRecovery_NormalExecution(t *testing.T) {
	ctx := context.Background()
	var executed bool
	var wg sync.WaitGroup
	wg.Add(1)

	GoroutineWithRecovery(ctx, func() {
		executed = true
		wg.Done()
	})

	// Wait for goroutine to complete
	done := make(chan struct{})
	go func() {
		wg.Wait()
		close(done)
	}()

	select {
	case <-done:
		assert.True(t, executed)
	case <-time.After(time.Second):
		t.Fatal("Goroutine did not complete in time")
	}
}

func TestGoroutineWithRecovery_PanicRecovery(t *testing.T) {
	ctx := context.Background()
	var recovered bool
	var wg sync.WaitGroup
	wg.Add(1)

	GoroutineWithRecovery(ctx, func() {
		defer wg.Done()
		recovered = true
		panic("test panic")
	})

	// Wait for goroutine to complete
	done := make(chan struct{})
	go func() {
		wg.Wait()
		close(done)
	}()

	select {
	case <-done:
		// Goroutine completed (panic was recovered)
		assert.True(t, recovered)
	case <-time.After(time.Second):
		t.Fatal("Goroutine did not complete in time")
	}
}

func TestGoroutineWithRecovery_MultipleGoroutines(t *testing.T) {
	ctx := context.Background()
	var counter int
	var mu sync.Mutex
	var wg sync.WaitGroup

	for i := 0; i < 10; i++ {
		wg.Add(1)
		GoroutineWithRecovery(ctx, func() {
			defer wg.Done()
			mu.Lock()
			counter++
			mu.Unlock()
		})
	}

	// Wait for all goroutines to complete
	done := make(chan struct{})
	go func() {
		wg.Wait()
		close(done)
	}()

	select {
	case <-done:
		assert.Equal(t, 10, counter)
	case <-time.After(2 * time.Second):
		t.Fatal("Goroutines did not complete in time")
	}
}
