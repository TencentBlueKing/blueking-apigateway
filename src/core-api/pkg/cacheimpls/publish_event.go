package cacheimpls

import (
	"context"
	"fmt"
)

// PublishEventKey is the key of publish event
type PublishEventKey struct {
	GatewayID int64
	StageID   int64
	PublishID int64
	Step      int
	Status    string
}

// Key return the key string of publish event
func (k PublishEventKey) Key() string {
	return fmt.Sprintf("%d:%d:%d:%d:%s", k.GatewayID, k.StageID, k.PublishID, k.Step, k.Status)
}

// PublishEventExists will heck if event exists
func PublishEventExists(ctx context.Context, key PublishEventKey) bool {
	k := key.Key()
	_, ok := publishEventCache.Get(k)
	return ok
}

// PublishEventSet will set event in cache
func PublishEventSet(ctx context.Context, key PublishEventKey) {
	publishEventCache.Set(key.Key(), struct{}{}, 0)
}
