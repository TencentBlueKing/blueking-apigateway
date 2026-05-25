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

// Package utils  contains some common utils
package utils

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

// BadRequestError ...
const (
	BadRequestError   = "BadRequest"
	UnauthorizedError = "Unauthorized"
	ForbiddenError    = "Forbidden"
	NotFoundError     = "NotFound"
	ConflictError     = "Conflict"
	TooManyRequests   = "TooManyRequests"

	SystemError = "InternalServerError"
)

// CommonResp is the common response structure for the API.
type CommonResp struct {
	Data  any `json:"data"`
	Error struct {
		Code    string `json:"code"`
		Message string `json:"message"`
		System  string `json:"system"`
	} `json:"error"`
}

// SuccessJSONResponse ...
func SuccessJSONResponse(c *gin.Context, data any) {
	c.JSON(http.StatusOK, gin.H{
		"data": data,
	})
}

// BaseErrorJSONResponse ...
func BaseErrorJSONResponse(c *gin.Context, errorCode, message string, statusCode int) {
	// BaseJSONResponse(c, statusCode, code, message, gin.H{})
	c.JSON(statusCode, gin.H{
		"error": gin.H{
			"code":    errorCode,
			"message": message,
			"system":  "bk-operator",
		},
	})
}

// NewErrorJSONResponse ...
func NewErrorJSONResponse(
	errorCode string,
	statusCode int,
) func(c *gin.Context, message string) {
	return func(c *gin.Context, message string) {
		BaseErrorJSONResponse(c, errorCode, message, statusCode)
	}
}

// BadRequestErrorJSONResponse ...
var (
	BadRequestErrorJSONResponse = NewErrorJSONResponse(BadRequestError, http.StatusBadRequest)
	ForbiddenJSONResponse       = NewErrorJSONResponse(ForbiddenError, http.StatusForbidden)
	UnauthorizedJSONResponse    = NewErrorJSONResponse(UnauthorizedError, http.StatusUnauthorized)
	NotFoundJSONResponse        = NewErrorJSONResponse(NotFoundError, http.StatusNotFound)
	ConflictJSONResponse        = NewErrorJSONResponse(ConflictError, http.StatusConflict)
	TooManyRequestsJSONResponse = NewErrorJSONResponse(TooManyRequests, http.StatusTooManyRequests)
)
