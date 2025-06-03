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
	"time"

	"github.com/gin-gonic/gin"
	jwt "github.com/golang-jwt/jwt/v4"
	"github.com/spf13/cast"

	"mcp_proxy/pkg/biz"
	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/constant"
	"mcp_proxy/pkg/util"
)

// AppInfo ...
type AppInfo struct {
	AppCode  string `json:"app_code"`
	Verified bool   `json:"verified"`
}

// UserInfo ...
type UserInfo struct {
	Verified bool   `json:"verified"`
	Username string `json:"username"`
}

// CustomClaims ...
type CustomClaims struct {
	App  AppInfo  `json:"app"`
	User UserInfo `json:"user"`
	jwt.RegisteredClaims
}

// ErrUnauthorized ...
var (
	ErrUnauthorized = errors.New("jwtauth: token is unauthorized")

	ErrExpired    = errors.New("jwtauth: token is expired")
	ErrNBFInvalid = errors.New("jwtauth: token nbf validation failed")
	ErrIATInvalid = errors.New("jwtauth: token iat validation failed")

	ErrAPIGatewayJWTAppInfoNoAppCode   = errors.New("app_code not in app info")
	ErrAPIGatewayJWTUserInfoNoUsername = errors.New("username not in user info")
	ErrAPIGatewayJWTAppNotVerified     = errors.New("app not verified")
	ErrAPIGatewayJWTUserNotVerified    = errors.New("user not verified")
)

// BkGatewayJWTAuthMiddleware is the middleware to verify the bk gateway jwt
func BkGatewayJWTAuthMiddleware() func(c *gin.Context) {
	return func(c *gin.Context) {
		signedToken := c.GetHeader(constant.BkGatewayJWTHeaderKey)
		if signedToken == "" {
			util.UnauthorizedJSONResponse(c, "no authorization credentials provided")
			c.Abort()
			return
		}
		jwtInfo, err := biz.GetJWTInfoByGatewayName(c.Request.Context(), constant.OfficialGatewayName)
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
		claims, err := parseBKJWTToken(signedToken, []byte(jwtInfo.PublicKey))
		if err != nil {
			util.UnauthorizedJSONResponse(c, err.Error())
			c.Abort()
			return
		}
		// verify token
		err = verifyJWTToken(claims)
		if err != nil {
			util.UnauthorizedJSONResponse(c, err.Error())
			c.Abort()
			return
		}
		util.SetBkAppCode(c, claims.App.AppCode)
		util.SetBkUsername(c, claims.User.Username)

		// sign inner jwt
		err = SignBkInnerJWTToken(c, claims, []byte(jwtInfo.PrivateKey))
		if err != nil {
			util.SystemErrorJSONResponse(c, err)
			c.Abort()
			return
		}
		util.SetInnerJWTToken(c, signedToken)
		util.SetBkApiTimeout(c, cast.ToInt(c.Request.Header.Get(constant.BkApiTimeoutHeaderKey)))
		c.Next()
	}
}

// SignBkInnerJWTToken ...
func SignBkInnerJWTToken(c *gin.Context, claims *CustomClaims, privateKey []byte) error {
	innerJwtClaims := CustomClaims{
		App: AppInfo{
			AppCode:  fmt.Sprintf(constant.BkVirtualAppCodeFormat, util.GetMCPServerID(c), claims.App.AppCode),
			Verified: claims.App.Verified,
		},
		User: UserInfo{
			Verified: claims.User.Verified,
			Username: claims.User.Username,
		},
		RegisteredClaims: jwt.RegisteredClaims{
			Issuer:    claims.Issuer,                                                             // 签发人
			Audience:  claims.Audience,                                                           // 签发目标
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(config.G.McpServer.InnerJwtExpireTime)), // 过期时间
			NotBefore: jwt.NewNumericDate(time.Now().Add(time.Second)),                           // 生效时间
			IssuedAt:  jwt.NewNumericDate(time.Now()),                                            // 签发时间
		},
	}
	token, err := jwt.NewWithClaims(jwt.SigningMethodHS256, innerJwtClaims).SignedString(privateKey)
	if err != nil {
		return err
	}
	// set inner jwt to context
	util.SetInnerJWTToken(c, token)
	return nil
}

// BKJWTAuthMiddleware parse the bk jwt
func parseBKJWTToken(tokenString string, publicKey []byte) (*CustomClaims, error) {
	keyFunc := func(token *jwt.Token) (interface{}, error) {
		pubKey, err := jwt.ParseRSAPublicKeyFromPEM(publicKey)
		if err != nil {
			return pubKey, fmt.Errorf("jwt parse fail, err=%w", err)
		}
		return pubKey, nil
	}
	claims := &CustomClaims{}
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

// verifyJWTToken verify the jwtToken
func verifyJWTToken(claims *CustomClaims) error {
	// verify app info
	if claims.App.AppCode == "" {
		return ErrAPIGatewayJWTAppInfoNoAppCode
	}
	if !claims.App.Verified {
		return ErrAPIGatewayJWTAppNotVerified
	}

	// verify user info
	if claims.User.Username == "" {
		return ErrAPIGatewayJWTUserInfoNoUsername
	}
	if claims.User.Verified {
		return ErrAPIGatewayJWTUserNotVerified
	}

	return nil
}
