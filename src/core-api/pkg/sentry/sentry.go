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

package sentry

import (
	"fmt"
	"time"

	raven "github.com/getsentry/raven-go"
	sentry "github.com/getsentry/sentry-go"

	"core/pkg/config"
)

var s Sentry

type Sentry struct {
	enabled bool
}

func Init(config config.Sentry) error {
	if config.DSN != "" {
		err := sentry.Init(sentry.ClientOptions{
			Dsn: config.DSN,
		})
		if err != nil {
			return fmt.Errorf("init sentry fail: %s", err)
		}

		// init gin sentry
		err = raven.SetDSN(config.DSN)
		if err != nil {
			return fmt.Errorf("init gin sentry fail: %s", err)
		}
		s.enabled = true
	}
	return nil
}

// Enabled  return if sentry is enabled
func Enabled() bool {
	return s.enabled
}

// ReportToSentry report to sentry
func ReportToSentry(message string, extra map[string]interface{}) {
	if s.enabled {
		// report to sentry
		ev := sentry.NewEvent()
		ev.Message = message
		ev.Level = "error"
		ev.Timestamp = time.Now()
		ev.Extra = extra
		sentry.CaptureEvent(ev)
	}
}
