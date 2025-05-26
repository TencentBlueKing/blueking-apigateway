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

package util

import (
	"fmt"
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

// SuccessResponse ...
type SuccessResponse struct {
	Data interface{} `json:"data"`
}

// Error ...
type Error struct {
	Code    string `json:"code"`
	Message string `json:"message"`
	System  string `json:"system"`
}

// ErrorResponse  ...
type ErrorResponse struct {
	Error Error `json:"error"`
}

// LegacySuccessResponse  ...
type LegacySuccessResponse struct {
	Data    interface{} `json:"data"`
	Result  bool        `json:"result"`
	Message string      `json:"message"`
	Code    int         `json:"code"`
}

// LegacyErrorResponse  ...
type LegacyErrorResponse struct {
	Result  bool   `json:"result"`
	Message string `json:"message"`
	Code    int    `json:"code"`
}

// SuccessJSONResponse ...
func SuccessJSONResponse(c *gin.Context, data interface{}) {
	c.JSON(http.StatusOK, SuccessResponse{
		Data: data,
	})
}

// BaseErrorJSONResponse ...
func BaseErrorJSONResponse(c *gin.Context, errorCode string, message string, statusCode int) {
	// BaseJSONResponse(c, statusCode, code, message, gin.H{})
	c.JSON(statusCode, ErrorResponse{Error: Error{
		Code:    errorCode,
		Message: message,
		System:  "bk-apigateway",
	}})
}

// NewErrorSeeResponse ...
func NewErrorSeeResponse(
	errorCode string,
	statusCode int,
) func(c *gin.Context, message string) {
	return func(c *gin.Context, message string) {
		BaseErrorJSONResponse(c, errorCode, message, statusCode)
	}
}

// BadRequestErrorJSONResponse ...
var (
	BadRequestErrorJSONResponse = NewErrorSeeResponse(BadRequestError, http.StatusBadRequest)
	ForbiddenJSONResponse       = NewErrorSeeResponse(ForbiddenError, http.StatusForbidden)
	UnauthorizedJSONResponse    = NewErrorSeeResponse(UnauthorizedError, http.StatusUnauthorized)
	NotFoundJSONResponse        = NewErrorSeeResponse(NotFoundError, http.StatusNotFound)
	ConflictJSONResponse        = NewErrorSeeResponse(ConflictError, http.StatusConflict)
	TooManyRequestsJSONResponse = NewErrorSeeResponse(TooManyRequests, http.StatusTooManyRequests)
)

// SystemErrorJSONResponse ...
func SystemErrorJSONResponse(c *gin.Context, err error) {
	message := fmt.Sprintf("system error[request_id=%s]: %s", GetRequestID(c), err.Error())

	BaseErrorJSONResponse(c, SystemError, message, http.StatusInternalServerError)
}
