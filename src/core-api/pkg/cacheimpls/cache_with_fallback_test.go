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
	"context"
	"database/sql"
	"errors"
	"testing"
	"time"

	"github.com/TencentBlueKing/gopkg/cache"
	"github.com/stretchr/testify/assert"
)

// testCacheKey is a simple cache key for testing
type testCacheKey struct {
	key string
}

func (k testCacheKey) Key() string {
	return k.key
}

func TestCacheWithFallback_Get(t *testing.T) {
	t.Parallel()

	t.Run("success from primary cache", func(t *testing.T) {
		t.Parallel()

		expectedValue := "test_value"
		retrieveFunc := func(ctx context.Context, key cache.Key) (any, error) {
			return expectedValue, nil
		}

		c := NewCacheWithFallback(
			"test_cache",
			retrieveFunc,
			5*time.Minute,
			nil,
			30*time.Minute,
		)

		key := testCacheKey{key: "test_key"}
		value, err := c.Get(context.Background(), key)

		assert.NoError(t, err)
		assert.Equal(t, expectedValue, value)

		// Verify value is also in fallback cache
		fallbackValue, found := c.fallback.Get(key.Key())
		assert.True(t, found)
		assert.Equal(t, expectedValue, fallbackValue)
	})

	t.Run("fallback on primary error", func(t *testing.T) {
		t.Parallel()

		callCount := 0
		expectedValue := "cached_value"
		retrieveFunc := func(ctx context.Context, key cache.Key) (any, error) {
			callCount++
			if callCount == 1 {
				return expectedValue, nil
			}
			return nil, errors.New("database error")
		}

		c := NewCacheWithFallback(
			"test_cache",
			retrieveFunc,
			1*time.Millisecond, // Very short expiration
			nil,
			30*time.Minute,
		)

		key := testCacheKey{key: "test_key"}

		// First call - should succeed and populate fallback
		value, err := c.Get(context.Background(), key)
		assert.NoError(t, err)
		assert.Equal(t, expectedValue, value)

		// Wait for primary cache to expire
		time.Sleep(10 * time.Millisecond)

		// Second call - primary fails, should fallback
		value, err = c.Get(context.Background(), key)
		assert.NoError(t, err)
		assert.Equal(t, expectedValue, value)
	})

	t.Run("error when both primary and fallback miss", func(t *testing.T) {
		t.Parallel()

		expectedErr := errors.New("retrieve error")
		retrieveFunc := func(ctx context.Context, key cache.Key) (any, error) {
			return nil, expectedErr
		}

		c := NewCacheWithFallback(
			"test_cache",
			retrieveFunc,
			5*time.Minute,
			nil,
			30*time.Minute,
		)

		key := testCacheKey{key: "test_key"}
		value, err := c.Get(context.Background(), key)

		assert.Error(t, err)
		assert.Nil(t, value)
	})

	t.Run("nil value cached properly", func(t *testing.T) {
		t.Parallel()

		retrieveFunc := func(ctx context.Context, key cache.Key) (any, error) {
			return nil, nil
		}

		c := NewCacheWithFallback(
			"test_cache",
			retrieveFunc,
			5*time.Minute,
			nil,
			30*time.Minute,
		)

		key := testCacheKey{key: "test_key"}
		value, err := c.Get(context.Background(), key)

		assert.NoError(t, err)
		assert.Nil(t, value)

		// Verify nil value is also in fallback cache
		fallbackValue, found := c.fallback.Get(key.Key())
		assert.True(t, found)
		assert.Nil(t, fallbackValue)
	})

	t.Run("sql.ErrNoRows should not fallback even with cached data", func(t *testing.T) {
		t.Parallel()

		callCount := 0
		expectedValue := "old_value"
		retrieveFunc := func(ctx context.Context, key cache.Key) (any, error) {
			callCount++
			if callCount == 1 {
				return expectedValue, nil
			}
			return nil, sql.ErrNoRows
		}

		c := NewCacheWithFallback(
			"test_cache",
			retrieveFunc,
			1*time.Millisecond, // Very short expiration
			nil,
			30*time.Minute,
		)

		key := testCacheKey{key: "test_key"}

		// First call - should succeed and populate fallback
		value, err := c.Get(context.Background(), key)
		assert.NoError(t, err)
		assert.Equal(t, expectedValue, value)

		// Verify fallback has the value
		fallbackValue, found := c.fallback.Get(key.Key())
		assert.True(t, found)
		assert.Equal(t, expectedValue, fallbackValue)

		// Wait for primary cache to expire
		time.Sleep(10 * time.Millisecond)

		// Second call - sql.ErrNoRows should NOT use fallback
		value, err = c.Get(context.Background(), key)
		assert.Error(t, err)
		assert.True(t, errors.Is(err, sql.ErrNoRows))
		assert.Nil(t, value)
	})

	t.Run("sql.ErrNoRows without fallback data", func(t *testing.T) {
		t.Parallel()

		retrieveFunc := func(ctx context.Context, key cache.Key) (any, error) {
			return nil, sql.ErrNoRows
		}

		c := NewCacheWithFallback(
			"test_cache",
			retrieveFunc,
			5*time.Minute,
			nil,
			30*time.Minute,
		)

		key := testCacheKey{key: "test_key"}
		value, err := c.Get(context.Background(), key)

		assert.Error(t, err)
		assert.True(t, errors.Is(err, sql.ErrNoRows))
		assert.Nil(t, value)
	})
}

func TestCacheWithFallback_Set(t *testing.T) {
	t.Parallel()

	t.Run("set stores in both caches", func(t *testing.T) {
		t.Parallel()

		retrieveFunc := func(ctx context.Context, key cache.Key) (any, error) {
			return nil, errors.New("should not be called")
		}

		c := NewCacheWithFallback(
			"test_cache",
			retrieveFunc,
			5*time.Minute,
			nil,
			30*time.Minute,
		)

		key := testCacheKey{key: "test_key"}
		expectedValue := "set_value"

		c.Set(context.Background(), key, expectedValue)

		// Verify value is in primary cache
		primaryValue, found := c.primary.DirectGet(context.Background(), key)
		assert.True(t, found)
		assert.Equal(t, expectedValue, primaryValue)

		// Verify value is in fallback cache
		fallbackValue, found := c.fallback.Get(key.Key())
		assert.True(t, found)
		assert.Equal(t, expectedValue, fallbackValue)
	})

	t.Run("set with nil value", func(t *testing.T) {
		t.Parallel()

		retrieveFunc := func(ctx context.Context, key cache.Key) (any, error) {
			return nil, errors.New("should not be called")
		}

		c := NewCacheWithFallback(
			"test_cache",
			retrieveFunc,
			5*time.Minute,
			nil,
			30*time.Minute,
		)

		key := testCacheKey{key: "test_key"}

		c.Set(context.Background(), key, nil)

		// Verify nil value is in fallback cache
		fallbackValue, found := c.fallback.Get(key.Key())
		assert.True(t, found)
		assert.Nil(t, fallbackValue)
	})
}

func TestCacheWithFallback_Delete(t *testing.T) {
	t.Parallel()

	t.Run("delete removes from both caches", func(t *testing.T) {
		t.Parallel()

		retrieveFunc := func(ctx context.Context, key cache.Key) (any, error) {
			return "value", nil
		}

		c := NewCacheWithFallback(
			"test_cache",
			retrieveFunc,
			5*time.Minute,
			nil,
			30*time.Minute,
		)

		key := testCacheKey{key: "test_key"}

		// First, set a value
		c.Set(context.Background(), key, "test_value")

		// Verify value exists in both caches
		_, found := c.primary.DirectGet(context.Background(), key)
		assert.True(t, found)
		_, found = c.fallback.Get(key.Key())
		assert.True(t, found)

		// Delete the value
		err := c.Delete(context.Background(), key)
		assert.NoError(t, err)

		// Verify value is removed from fallback cache
		_, found = c.fallback.Get(key.Key())
		assert.False(t, found)

		// Verify value is removed from primary cache
		_, found = c.primary.DirectGet(context.Background(), key)
		assert.False(t, found)
	})

	t.Run("delete non-existent key", func(t *testing.T) {
		t.Parallel()

		retrieveFunc := func(ctx context.Context, key cache.Key) (any, error) {
			return nil, nil
		}

		c := NewCacheWithFallback(
			"test_cache",
			retrieveFunc,
			5*time.Minute,
			nil,
			30*time.Minute,
		)

		key := testCacheKey{key: "non_existent_key"}

		// Delete should not error on non-existent key
		err := c.Delete(context.Background(), key)
		assert.NoError(t, err)
	})
}
