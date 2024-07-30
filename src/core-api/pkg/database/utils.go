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

package database

import (
	"database/sql"
	"fmt"
	"strings"
	"time"

	"github.com/TencentBlueKing/gopkg/stringx"
	"github.com/jmoiron/sqlx"
	jsoniter "github.com/json-iterator/go"
	"go.uber.org/zap"

	"core/pkg/logging"
)

// ArgsTruncateLength ...
const (
	ArgsTruncateLength = 4096
)

// ============== tx Rollback Log ==============

// RollBackWithLog will rollback and log if error
func RollBackWithLog(tx *sqlx.Tx) {
	err := tx.Rollback()
	if err != sql.ErrTxDone && err != nil {
		logging.GetLogger().Error(err)
	}
}

// ============== slow sql logger ==============
func logSlowSQL(start time.Time, query string, args interface{}) {
	elapsed := time.Since(start)
	// to ms
	latency := float64(elapsed / time.Millisecond)

	query = strings.ReplaceAll(query, "\n", "")
	query = strings.ReplaceAll(query, "\t", " ")
	query = strings.ReplaceAll(query, "  ", " ")

	// current, set 20ms
	if logging.GetLogger().Level() == zap.DebugLevel {
		logging.GetLogger().Infow(
			"Slow SQL",
			"sql", query,
			"args", truncateArgs(args, ArgsTruncateLength),
			"latency", latency,
		)
	}

	if latency > 20 {
		// err will send to sentry
		logging.GetLogger().Errorw(
			"Slow SQL",
			"sql", query,
			"args", truncateArgs(args, ArgsTruncateLength),
			"latency", latency,
		)
	}
}

func truncateArgs(args interface{}, length int) string {
	s, err := jsoniter.MarshalToString(args)
	if err != nil {
		s = fmt.Sprintf("%v", args)
	}
	return stringx.Truncate(s, length)
}
