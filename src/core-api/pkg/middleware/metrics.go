/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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

package middleware

import (
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/prometheus/client_golang/prometheus"

	"core/pkg/metric"
)

// Metrics ...
func Metrics() gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()

		c.Next()

		duration := time.Since(start)
		status := strconv.Itoa(c.Writer.Status())
		metric.RequestCount.With(prometheus.Labels{
			"method": c.Request.Method,
			"path":   c.FullPath(),
			"status": status,
		}).Inc()

		// request duration, in ms
		metric.RequestDuration.With(prometheus.Labels{
			"method": c.Request.Method,
			"path":   c.FullPath(),
			"status": status,
		}).Observe(float64(duration) / float64(time.Microsecond))
	}
}
