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

package model

// Gateway ...
type Gateway struct {
	ID   int    `gorm:"primaryKey;autoIncrement;column:id"`
	Name string `gorm:"column:name;size:64;uniqueIndex"`
}

// TableName ...
func (Gateway) TableName() string {
	return "core_api"
}

// Stage ...
type Stage struct {
	ID   int    `gorm:"primaryKey;autoIncrement;column:id"`
	Name string `gorm:"column:name"`
}

// TableName ...
func (Stage) TableName() string {
	return "core_stage"
}

// JWT ...
type JWT struct {
	GatewayID           int    `gorm:"column:api_id;primaryKey"`
	PrivateKey          string `gorm:"column:private_key;type:longtext"`
	PublicKey           string `gorm:"column:public_key;type:longtext"`
	EncryptedPrivateKey string `gorm:"column:encrypted_private_key;type:longtext"`
}

// TableName ...
func (JWT) TableName() string {
	return "core_jwt"
}

// Release ...
type Release struct {
	ID                int `gorm:"primaryKey;autoIncrement;column:id"`
	GatewayID         int `gorm:"column:api_id"`
	ResourceVersionID int `gorm:"column:resource_version_id"`
	StageID           int `gorm:"column:stage_id;uniqueIndex"`
}

// TableName ...
func (Release) TableName() string {
	return "core_release"
}

// ReleasedResource ...
type ReleasedResource struct {
	ID                int    `gorm:"primaryKey;autoIncrement;column:id"`
	ResourceVersionID int    `gorm:"column:resource_version_id"`
	ResourceID        int    `gorm:"column:resource_id"`
	ResourceName      string `gorm:"column:resource_name;size:256"`
	ResourceMethod    string `gorm:"column:resource_method;size:10"`
	ResourcePath      string `gorm:"column:resource_path;size:2048"`
	GatewayID         int    `gorm:"column:api_id;uniqueIndex:idx_api_resver_resid"`
	Data              string `gorm:"column:data;type:longtext"`
}

// TableName ...
func (ReleasedResource) TableName() string {
	return "core_released_resource"
}

// Resource ...
type Resource struct {
	ID                   int    `gorm:"primaryKey;autoIncrement;column:id"`
	Name                 string `gorm:"column:name;size:256"`
	Description          string `gorm:"column:description;size:512"`
	Method               string `gorm:"column:method;size:10"`
	Path                 string `gorm:"column:path;size:2048"`
	ProxyID              int    `gorm:"column:proxy_id"`
	IsPublic             bool   `gorm:"column:is_public"`
	GatewayID            int    `gorm:"column:api_id"`
	MatchSubpath         bool   `gorm:"column:match_subpath"`
	AllowApplyPermission bool   `gorm:"column:allow_apply_permission"`
	DescriptionEn        string `gorm:"column:description_en;size:512"`
	EnableWebsocket      bool   `gorm:"column:enable_websocket"`
}

// TableName ...
func (Resource) TableName() string {
	return "core_resource"
}

// ResourceVersion ...
type ResourceVersion struct {
	ID            int    `gorm:"primaryKey;autoIncrement;column:id"`
	Data          string `gorm:"column:data;type:longtext"`
	GatewayID     int64  `gorm:"column:api_id"`
	Version       string `gorm:"column:version;size:128"`
	SchemaVersion string `gorm:"column:schema_version;size:32;default:'1.0'"`
}

// TableName ...
func (ResourceVersion) TableName() string {
	return "core_resource_version"
}

// OpenapiGatewayResourceVersionSpec ...
type OpenapiGatewayResourceVersionSpec struct {
	ID                int    `gorm:"primaryKey;autoIncrement;column:id"`
	Schema            string `gorm:"column:schema;type:longtext"`
	GatewayID         int    `gorm:"column:api_id"`
	ResourceVersionID int    `gorm:"column:resource_version_id;unique"`
}

// TableName ...
func (OpenapiGatewayResourceVersionSpec) TableName() string {
	return "openapi_gateway_resource_version_spec"
}
