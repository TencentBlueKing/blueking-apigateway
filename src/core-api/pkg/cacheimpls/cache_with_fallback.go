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
	"time"

	"github.com/TencentBlueKing/gopkg/cache"
	"github.com/TencentBlueKing/gopkg/cache/memory"
	"github.com/TencentBlueKing/gopkg/cache/memory/backend"
	gocache "github.com/patrickmn/go-cache"

	"core/pkg/logging"
)

// CacheWithFallback wraps a primary cache with a fallback cache.
// When the primary cache fails to retrieve data (e.g., DB error),
// it falls back to the secondary cache with a longer TTL.
type CacheWithFallback struct {
	name        string
	primary     memory.Cache
	fallback    *gocache.Cache
	fallbackTTL time.Duration
}

// NewCacheWithFallback creates a new cache with fallback capability.
// - name: the cache name
// - retrieveFunc: the function to retrieve the real data
// - expiration: the primary cache expiration time
// - randomExtraExpirationFunc: the function to generate random extra expiration duration
// - fallbackTTL: the fallback cache TTL (should be longer than primary)
// - options: additional options for the primary cache
// NOTE: only Get/Set/Delete with fallback logic, other methods are not supported
func NewCacheWithFallback(
	name string,
	retrieveFunc memory.RetrieveFunc,
	expiration time.Duration,
	randomExtraExpirationFunc backend.RandomExtraExpirationDurationFunc,
	fallbackTTL time.Duration,
) *CacheWithFallback {
	// Create primary cache with the same behavior as before
	primary := memory.NewCache(name, retrieveFunc, expiration, randomExtraExpirationFunc)

	// Create fallback cache with longer TTL
	// Cleanup interval is fallbackTTL + 5 minutes
	fallback := gocache.New(fallbackTTL, fallbackTTL+5*time.Minute)

	return &CacheWithFallback{
		name:        name,
		primary:     primary,
		fallback:    fallback,
		fallbackTTL: fallbackTTL,
	}
}

// Get retrieves a value from the cache.
// If the primary cache succeeds, the value is also stored in the fallback cache.
// If the primary cache fails (e.g., DB error), it tries to return the fallback value.
// NOTE: only fallback if the error is not sql.ErrNoRows
func (c *CacheWithFallback) Get(ctx context.Context, key cache.Key) (any, error) {
	value, err := c.primary.Get(ctx, key)
	if err == nil {
		// Success: store value (including nil) in fallback cache
		c.fallback.Set(key.Key(), value, c.fallbackTTL)
		return value, nil
	}

	// err != nil

	// only fallback if the error is not sql.ErrNoRows
	if errors.Is(err, sql.ErrNoRows) {
		return nil, err
	}

	// not sql.ErrNoRows, try fallback cache
	if fallbackValue, found := c.fallback.Get(key.Key()); found {
		logging.GetLogger().Warnw("using fallback cache due to error",
			"cache", c.name, "key", key.Key(), "error", err)
		return fallbackValue, nil // fallbackValue can be nil
	}

	return nil, err
}

// Set stores a value in both the primary and fallback caches.
func (c *CacheWithFallback) Set(ctx context.Context, key cache.Key, data any) {
	c.primary.Set(ctx, key, data)
	c.fallback.Set(key.Key(), data, c.fallbackTTL)
}

// Delete removes a value from both the primary and fallback caches.
func (c *CacheWithFallback) Delete(ctx context.Context, key cache.Key) error {
	c.fallback.Delete(key.Key())
	return c.primary.Delete(ctx, key)
}

// DirectGet gets a value directly from the primary cache without triggering retrieval.
func (c *CacheWithFallback) DirectGet(ctx context.Context, key cache.Key) (any, bool) {
	return c.primary.DirectGet(ctx, key)
}

// Exists checks if a key exists in the primary cache.
func (c *CacheWithFallback) Exists(ctx context.Context, key cache.Key) bool {
	return c.primary.Exists(ctx, key)
}

// Disabled returns whether the primary cache is disabled.
func (c *CacheWithFallback) Disabled() bool {
	return c.primary.Disabled()
}

// GetString returns a string value from the cache.
func (c *CacheWithFallback) GetString(ctx context.Context, key cache.Key) (string, error) {
	return c.primary.GetString(ctx, key)
}

// GetBool returns a bool value from the cache.
func (c *CacheWithFallback) GetBool(ctx context.Context, key cache.Key) (bool, error) {
	return c.primary.GetBool(ctx, key)
}

// GetInt returns an int value from the cache.
func (c *CacheWithFallback) GetInt(ctx context.Context, key cache.Key) (int, error) {
	return c.primary.GetInt(ctx, key)
}

// GetInt8 returns an int8 value from the cache.
func (c *CacheWithFallback) GetInt8(ctx context.Context, key cache.Key) (int8, error) {
	return c.primary.GetInt8(ctx, key)
}

// GetInt16 returns an int16 value from the cache.
func (c *CacheWithFallback) GetInt16(ctx context.Context, key cache.Key) (int16, error) {
	return c.primary.GetInt16(ctx, key)
}

// GetInt32 returns an int32 value from the cache.
func (c *CacheWithFallback) GetInt32(ctx context.Context, key cache.Key) (int32, error) {
	return c.primary.GetInt32(ctx, key)
}

// GetInt64 returns an int64 value from the cache.
func (c *CacheWithFallback) GetInt64(ctx context.Context, key cache.Key) (int64, error) {
	return c.primary.GetInt64(ctx, key)
}

// GetUint returns a uint value from the cache.
func (c *CacheWithFallback) GetUint(ctx context.Context, key cache.Key) (uint, error) {
	return c.primary.GetUint(ctx, key)
}

// GetUint8 returns a uint8 value from the cache.
func (c *CacheWithFallback) GetUint8(ctx context.Context, key cache.Key) (uint8, error) {
	return c.primary.GetUint8(ctx, key)
}

// GetUint16 returns a uint16 value from the cache.
func (c *CacheWithFallback) GetUint16(ctx context.Context, key cache.Key) (uint16, error) {
	return c.primary.GetUint16(ctx, key)
}

// GetUint32 returns a uint32 value from the cache.
func (c *CacheWithFallback) GetUint32(ctx context.Context, key cache.Key) (uint32, error) {
	return c.primary.GetUint32(ctx, key)
}

// GetUint64 returns a uint64 value from the cache.
func (c *CacheWithFallback) GetUint64(ctx context.Context, key cache.Key) (uint64, error) {
	return c.primary.GetUint64(ctx, key)
}

// GetFloat32 returns a float32 value from the cache.
func (c *CacheWithFallback) GetFloat32(ctx context.Context, key cache.Key) (float32, error) {
	return c.primary.GetFloat32(ctx, key)
}

// GetFloat64 returns a float64 value from the cache.
func (c *CacheWithFallback) GetFloat64(ctx context.Context, key cache.Key) (float64, error) {
	return c.primary.GetFloat64(ctx, key)
}

// GetTime returns a time.Time value from the cache.
func (c *CacheWithFallback) GetTime(ctx context.Context, key cache.Key) (time.Time, error) {
	return c.primary.GetTime(ctx, key)
}
