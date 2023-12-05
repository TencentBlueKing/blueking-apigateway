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
	"database/sql"
	"errors"
	"fmt"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v4"
	"github.com/spf13/cast"

	"core/pkg/service"
	"core/pkg/util"
)

const (
	BkGatewayJWTHeaderKey = "X-Bkapi-Jwt"
	OfficialGatewayName   = "bk-apigateway"
)

var (
	ErrUnauthorized = errors.New("jwtauth: token is unauthorized")

	ErrExpired    = errors.New("jwtauth: token is expired")
	ErrNBFInvalid = errors.New("jwtauth: token nbf validation failed")
	ErrIATInvalid = errors.New("jwtauth: token iat validation failed")

	ErrAPIGatewayJWTMissingApp             = errors.New("app not in jwt claims")
	ErrAPIGatewayJWTAppInfoParseFail       = errors.New("app info parse fail")
	ErrAPIGatewayJWTAppInfoNoAppCode       = errors.New("app_code not in app info")
	ErrAPIGatewayJWTAppCodeNotString       = errors.New("app_code not string")
	ErrAPIGatewayJWTAppInfoNoVerified      = errors.New("verified not in app info")
	ErrAPIGatewayJWTAppInfoVerifiedNotBool = errors.New("verified not bool")
	ErrAPIGatewayJWTAppNotVerified         = errors.New("app not verified")
)

// BkGatewayJWTAuthMiddlewareV1  is the middleware to verify the bk gateway jwt
func BkGatewayJWTAuthMiddlewareV1() func(c *gin.Context) {
	return func(c *gin.Context) {
		signedToken := c.GetHeader(BkGatewayJWTHeaderKey)
		if signedToken == "" {
			util.LegacyErrorJSONResponse(
				c,
				util.UnauthorizedError,
				http.StatusUnauthorized,
				"no authorization credentials provided",
			)
			c.Abort()
			return
		}
		// get public key
		svc := service.NewGatewayPublicKeyService()
		publicKeyString, err := svc.GetByGatewayName(c.Request.Context(), OfficialGatewayName)
		if err != nil {
			if errors.Is(err, sql.ErrNoRows) {
				util.LegacyErrorJSONResponse(c, util.NotFoundError, http.StatusNotFound, err.Error())
				return
			}
			util.LegacyErrorJSONResponse(c, util.SystemError, http.StatusInternalServerError, err.Error())
			c.Abort()
			return
		}

		// parse token
		claims, err := parseBKJWTToken(signedToken, []byte(publicKeyString))
		if err != nil {
			util.LegacyErrorJSONResponse(c, util.UnauthorizedError, http.StatusUnauthorized, err.Error())
			c.Abort()
			return
		}
		// verify token
		err = verifyJwtToken(claims)
		if err != nil {
			util.LegacyErrorJSONResponse(c, util.UnauthorizedError, http.StatusUnauthorized, err.Error())
			c.Abort()
			return
		}
		// set issuer
		util.SetBkGatewayIssuer(c, cast.ToString(claims["iss"]))
		c.Next()
	}
}

// BkGatewayJWTAuthMiddlewareV2  is the middleware to verify the bk gateway jwt
func BkGatewayJWTAuthMiddlewareV2() func(c *gin.Context) {
	return func(c *gin.Context) {
		signedToken := c.GetHeader(BkGatewayJWTHeaderKey)
		if signedToken == "" {
			util.UnauthorizedJSONResponse(c, "no authorization credentials provided")
			c.Abort()
			return
		}
		// get public key
		svc := service.NewGatewayPublicKeyService()
		publicKeyString, err := svc.GetByGatewayName(c.Request.Context(), OfficialGatewayName)
		if err != nil {
			if errors.Is(err, sql.ErrNoRows) {
				util.NotFoundJSONResponse(c, err.Error())
				return
			}
			util.SystemErrorJSONResponse(c, err)
			c.Abort()
			return
		}

		// parse token
		claims, err := parseBKJWTToken(signedToken, []byte(publicKeyString))
		if err != nil {
			util.UnauthorizedJSONResponse(c, err.Error())
			c.Abort()
			return
		}
		// verify token
		err = verifyJwtToken(claims)
		if err != nil {
			util.UnauthorizedJSONResponse(c, err.Error())
			c.Abort()
			return
		}
		// set issuer
		util.SetBkGatewayIssuer(c, cast.ToString(claims["iss"]))
		c.Next()
	}
}

// BKJWTAuthMiddleware parse the bk jwt
func parseBKJWTToken(tokenString string, publicKey []byte) (jwt.MapClaims, error) {
	keyFunc := func(token *jwt.Token) (interface{}, error) {
		pubKey, err := jwt.ParseRSAPublicKeyFromPEM(publicKey)
		if err != nil {
			return pubKey, fmt.Errorf("jwt parse fail, err=%w", err)
		}
		return pubKey, nil
	}

	claims := jwt.MapClaims{}
	token, err := jwt.ParseWithClaims(tokenString, claims, keyFunc)
	if err != nil {
		var verr *jwt.ValidationError
		if errors.As(err, &verr) {
			switch {
			case verr.Errors&jwt.ValidationErrorExpired > 0:
				return nil, ErrExpired
			case verr.Errors&jwt.ValidationErrorIssuedAt > 0:
				return nil, ErrIATInvalid
			case verr.Errors&jwt.ValidationErrorNotValidYet > 0:
				return nil, ErrNBFInvalid
			}
		}
		return nil, err
	}

	if !token.Valid {
		return nil, ErrUnauthorized
	}

	return claims, nil
}

// verifyJwtToken verify the jwtToken
func verifyJwtToken(claims jwt.MapClaims) error {
	appInfo, ok := claims["app"]
	if !ok {
		return ErrAPIGatewayJWTMissingApp
	}
	app, ok := appInfo.(map[string]interface{})
	if !ok {
		return ErrAPIGatewayJWTAppInfoParseFail
	}

	verifiedRaw, ok := app["verified"]
	if !ok {
		return ErrAPIGatewayJWTAppInfoNoVerified
	}

	verified, ok := verifiedRaw.(bool)
	if !ok {
		return ErrAPIGatewayJWTAppInfoVerifiedNotBool
	}

	if !verified {
		return ErrAPIGatewayJWTAppNotVerified
	}
	return nil
}
