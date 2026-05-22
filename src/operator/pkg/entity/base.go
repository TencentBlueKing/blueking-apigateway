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

// Package entity ...
package entity

// GetBaseInfo 获取基本信	息
type GetBaseInfo interface {
	GetBaseInfo() *ResourceMetadata
}

// GetPlugins 获取插件
type GetPlugins interface {
	GetPlugins() map[string]any
}

// GetPlugins 获取插件
func (r *Route) GetPlugins() map[string]any {
	return r.Plugins
}

// GetPlugins 获取插件
func (s *Service) GetPlugins() map[string]any {
	return s.Plugins
}

// GetPlugins 获取插件
func (c *Consumer) GetPlugins() map[string]any {
	return c.Plugins
}

// GetPlugins 获取插件
func (g *GlobalRule) GetPlugins() map[string]any {
	return g.Plugins
}

// GetPlugins 获取插件
func (p *PluginConfig) GetPlugins() map[string]any {
	return p.Plugins
}
