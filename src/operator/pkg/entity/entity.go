/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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

package entity

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"

	"github.com/spf13/cast"
	"github.com/tidwall/gjson"
	"go.etcd.io/etcd/api/v3/mvccpb"

	"operator/pkg/config"
	"operator/pkg/constant"
)

// ApisixResource defines common function for apisix resources
type ApisixResource interface {
	GetID() string
	GetReleaseInfo() *ReleaseInfo
	GetStageName() string
	GetCreateTime() int64
	GetUpdateTime() int64
	SetCreateTime(int64)
	SetUpdateTime(int64)
	ClearUnusedFields()
}

// ApisixStageResource 网关环境资源配置
type ApisixStageResource struct {
	Routes   map[string]*Route   `json:"routes,omitempty"  yaml:"routes"`
	Services map[string]*Service `json:"services,omitempty" yaml:"services"`
	SSLs     map[string]*SSL     `json:"ssls,omitempty" yaml:"ssls"`
}

type ExtraApisixStageResource struct {
	Routes   []*Route   `json:"routes,omitempty" yaml:"routes"`
	Services []*Service `json:"services,omitempty" yaml:"services"`
	SSLs     []*SSL     `json:"ssls,omitempty" yaml:"ssls"`
}

// NewEmptyApisixConfiguration will build a new apisix configuration object
func NewEmptyApisixConfiguration() *ApisixStageResource {
	return &ApisixStageResource{
		Routes:   make(map[string]*Route),
		Services: make(map[string]*Service),
		SSLs:     make(map[string]*SSL),
	}
}

// NewEmptyApisixGlobalResource ...
func NewEmptyApisixGlobalResource() *ApisixGlobalResource {
	return &ApisixGlobalResource{
		PluginMetadata: make(map[string]*PluginMetadata),
	}
}

// ApisixGlobalResource 全局资源配置
type ApisixGlobalResource struct {
	PluginMetadata map[string]*PluginMetadata `json:"plugin_metadata,omitempty"`
}

// Status ...
type Status uint8

// Route ...
type Route struct {
	ResourceMetadata `yaml:",inline"`
	URI              string         `json:"uri,omitempty" yaml:"uri"`
	Uris             []string       `json:"uris,omitempty" yaml:"uris"`
	Priority         int            `json:"priority,omitempty" yaml:"priority"`
	Methods          []string       `json:"methods,omitempty" yaml:"methods"`
	Host             string         `json:"host,omitempty" yaml:"host"`
	Hosts            []string       `json:"hosts,omitempty" yaml:"hosts"`
	RemoteAddr       string         `json:"remote_addr,omitempty" yaml:"remote_addr"`
	RemoteAddrs      []string       `json:"remote_addrs,omitempty" yaml:"remote_addrs"`
	Vars             []any          `json:"vars,omitempty" yaml:"vars"`
	FilterFunc       string         `json:"filter_func,omitempty" yaml:"filter_func"`
	Script           any            `json:"script,omitempty" yaml:"script"`
	ScriptID         any            `json:"script_id,omitempty" yaml:"script_id"`
	Plugins          map[string]any `json:"plugins,omitempty" yaml:"plugins"`
	PluginConfigID   any            `json:"plugin_config_id,omitempty" yaml:"plugin_config_id"`
	Upstream         *UpstreamDef   `json:"upstream,omitempty" yaml:"upstream"`
	ServiceID        any            `json:"service_id,omitempty" yaml:"service_id"`
	UpstreamID       any            `json:"upstream_id,omitempty" yaml:"upstream_id"`
	ServiceProtocol  string         `json:"service_protocol,omitempty" yaml:"service_protocol"`
	EnableWebsocket  bool           `json:"enable_websocket,omitempty" yaml:"enable_websocket"`
	Status           Status         `json:"status" yaml:"status"`
	Timeout          *Timeout       `json:"timeout,omitempty" yaml:"timeout,omitempty"`
	CreateTime       int64          `json:"create_time,omitempty" yaml:"create_time,omitempty"`
	UpdateTime       int64          `json:"update_time,omitempty" yaml:"update_time,omitempty"`
}

// GetCreateTime ...
func (r *Route) GetCreateTime() int64 {
	return r.CreateTime
}

// GetUpdateTime ...
func (r *Route) GetUpdateTime() int64 {
	return r.UpdateTime
}

// SetCreateTime ...
func (r *Route) SetCreateTime(i int64) {
	r.CreateTime = i
}

// SetUpdateTime ...
func (r *Route) SetUpdateTime(i int64) {
	r.UpdateTime = i
}

// TimeoutValue ...
type (
	TimeoutValue float32
	Timeout      struct {
		Connect TimeoutValue `json:"connect,omitempty" yaml:"connect"`
		Send    TimeoutValue `json:"send,omitempty" yaml:"send"`
		Read    TimeoutValue `json:"read,omitempty" yaml:"read"`
	}
)

// Node ...
type Node struct {
	Host     string `json:"host,omitempty" yaml:"host"`
	Port     int    `json:"port,omitempty" yaml:"port"`
	Weight   int    `json:"weight" yaml:"weight"`
	Metadata any    `json:"metadata,omitempty" yaml:"metadata"`
	Priority int    `json:"priority,omitempty" yaml:"priority"`
}

// Healthy ...
type Healthy struct {
	Interval     int   `json:"interval,omitempty" yaml:"interval"`
	HttpStatuses []int `json:"http_statuses,omitempty" yaml:"http_statuses"`
	Successes    int   `json:"successes,omitempty" yaml:"successes"`
}

// UnHealthy ...
type UnHealthy struct {
	Interval     int   `json:"interval,omitempty" yaml:"interval"`
	HTTPStatuses []int `json:"http_statuses,omitempty" yaml:"http_statuses"`
	TCPFailures  int   `json:"tcp_failures,omitempty" yaml:"tcp_failures"`
	Timeouts     int   `json:"timeouts,omitempty" yaml:"timeouts"`
	HTTPFailures int   `json:"http_failures,omitempty" yaml:"http_failures"`
}

// Active ...
type Active struct {
	Type                   string       `json:"type,omitempty" yaml:"type"`
	Timeout                TimeoutValue `json:"timeout,omitempty" yaml:"timeout"`
	Concurrency            int          `json:"concurrency,omitempty" yaml:"concurrency"`
	Host                   string       `json:"host,omitempty" yaml:"host"`
	Port                   int          `json:"port,omitempty" yaml:"port"`
	HTTPPath               string       `json:"http_path,omitempty" yaml:"http_path"`
	HTTPSVerifyCertificate bool         `json:"https_verify_certificate,omitempty" yaml:"https_verify_certificate"`
	Healthy                Healthy      `json:"healthy,omitempty" yaml:"healthy"`
	UnHealthy              UnHealthy    `json:"unhealthy,omitempty" yaml:"unhealthy"`
	ReqHeaders             []string     `json:"req_headers,omitempty" yaml:"req_headers"`
}

// Passive ...
type Passive struct {
	Type      string    `json:"type,omitempty" yaml:"type"`
	Healthy   Healthy   `json:"healthy,omitempty"`
	UnHealthy UnHealthy `json:"unhealthy,omitempty"`
}

// HealthChecker ...
type HealthChecker struct {
	Active  Active  `json:"active,omitempty"`
	Passive Passive `json:"passive,omitempty"`
}

// UpstreamTLS ...
type UpstreamTLS struct {
	ClientCert   string `json:"client_cert,omitempty"`
	ClientKey    string `json:"client_key,omitempty"`
	ClientCertId string `json:"client_cert_id,omitempty"`
}

// UpstreamKeepalivePool ...
type UpstreamKeepalivePool struct {
	IdleTimeout *TimeoutValue `json:"idle_timeout,omitempty"`
	Requests    int           `json:"requests,omitempty"`
	Size        int           `json:"size"`
}

// UpstreamDef ...
type UpstreamDef struct {
	ResourceMetadata `yaml:",inline"`
	Nodes            any                    `json:"nodes,omitempty" yaml:"nodes"`
	Retries          *int                   `json:"retries,omitempty" yaml:"retries"`
	Timeout          *Timeout               `json:"timeout,omitempty" yaml:"timeout"`
	Type             string                 `json:"type,omitempty" yaml:"type"`
	Checks           any                    `json:"checks,omitempty" yaml:"checks"`
	HashOn           string                 `json:"hash_on,omitempty" yaml:"hash_on"`
	Key              string                 `json:"key,omitempty" yaml:"key"`
	Scheme           string                 `json:"scheme,omitempty" yaml:"scheme"`
	DiscoveryType    string                 `json:"discovery_type,omitempty" yaml:"discovery_type"`
	DiscoveryArgs    map[string]any         `json:"discovery_args,omitempty" yaml:"discovery_args"`
	PassHost         string                 `json:"pass_host,omitempty" yaml:"pass_host"`
	UpstreamHost     string                 `json:"upstream_host,omitempty" yaml:"upstream_host"`
	ServiceName      string                 `json:"service_name,omitempty" yaml:"service_name"`
	TLS              *UpstreamTLS           `json:"tls,omitempty" yaml:"tls"`
	KeepalivePool    *UpstreamKeepalivePool `json:"keepalive_pool,omitempty" yaml:"keepalive_pool"`
	RetryTimeout     TimeoutValue           `json:"retry_timeout,omitempty" yaml:"retry_timeout"`
}

// Upstream ...
type Upstream struct {
	UpstreamDef `yaml:",inline"`
}

// Consumer ...
type Consumer struct {
	Username string            `json:"username"`
	Desc     string            `json:"desc,omitempty"`
	Plugins  map[string]any    `json:"plugins,omitempty"`
	Labels   map[string]string `json:"labels,omitempty"`
	GroupID  string            `json:"group_id,omitempty"`
}

// ConsumerGroup ...
type ConsumerGroup struct {
	Desc       string            `json:"desc,omitempty"`
	Plugins    map[string]any    `json:"plugins,omitempty"`
	Labels     map[string]string `json:"labels,omitempty"`
	CreateTime int64             `json:"create_time,omitempty"`
	UpdateTime int64             `json:"update_time,omitempty"`
}

// Service ...
type Service struct {
	ResourceMetadata `yaml:",inline"`
	Upstream         *UpstreamDef   `json:"upstream,omitempty" yaml:"upstream"`
	UpstreamID       any            `json:"upstream_id,omitempty" yaml:"upstream_id"`
	Plugins          map[string]any `json:"plugins,omitempty" yaml:"plugins"`
	Script           string         `json:"script,omitempty" yaml:"script"`
	EnableWebsocket  bool           `json:"enable_websocket,omitempty" yaml:"enable_websocket"`
	Hosts            []string       `json:"hosts,omitempty" yaml:"hosts"`
	CreateTime       int64          `json:"create_time,omitempty" yaml:"create_time,omitempty"`
	UpdateTime       int64          `json:"update_time,omitempty" yaml:"update_time,omitempty"`
}

// GetCreateTime ...
func (s *Service) GetCreateTime() int64 {
	return s.CreateTime
}

// GetUpdateTime ...
func (s *Service) GetUpdateTime() int64 {
	return s.UpdateTime
}

// SetCreateTime sets the creation time for the service
// It takes an int64 parameter representing the timestamp
func (s *Service) SetCreateTime(i int64) {
	// Assign the provided timestamp to the CreateTime field of the Service
	s.CreateTime = i
}

// SetUpdateTime ...
func (s *Service) SetUpdateTime(i int64) {
	s.UpdateTime = i
}

// GlobalRule ...
type GlobalRule struct {
	ResourceMetadata `yaml:",inline"`
	Plugins          map[string]any `json:"plugins" yaml:"plugins"`
}

// PluginMetadataConf ...
type PluginMetadataConf map[string]json.RawMessage

// PluginMetadata ...
type PluginMetadata struct {
	ResourceMetadata
	PluginMetadataConf
}

// UnmarshalJSON 解析 PluginMetadataConf
func (p *PluginMetadataConf) UnmarshalJSON(conf []byte) error {
	pluginName := gjson.GetBytes(conf, "id").String()
	if pluginName == "" {
		return fmt.Errorf("plugin id is empty")
	}
	*p = PluginMetadataConf{pluginName: conf}
	return nil
}

// MarshalJSON 将 PluginMetadataConf 转换为 json
func (p *PluginMetadataConf) MarshalJSON() ([]byte, error) {
	for key, conf := range *p {
		if key != "" {
			return conf, nil
		}
	}
	return nil, errors.New("invalid plugin conf")
}

// ServerInfo ...
type ServerInfo struct {
	ResourceMetadata `yaml:",inline"`
	LastReportTime   int64  `json:"last_report_time,omitempty" yaml:"last_report_time"`
	UpTime           int64  `json:"up_time,omitempty" yaml:"up_time"`
	BootTime         int64  `json:"boot_time,omitempty" yaml:"boot_time"`
	EtcdVersion      string `json:"etcd_version,omitempty" yaml:"etcd_version"`
	Hostname         string `json:"hostname,omitempty" yaml:"hostname"`
	Version          string `json:"version,omitempty" yaml:"version"`
}

// PluginConfig ...
type PluginConfig struct {
	ResourceMetadata
	Desc    string         `json:"desc,omitempty"`
	Plugins map[string]any `json:"plugins"`
}

// SSLClient ...
type SSLClient struct {
	CA               string   `json:"ca,omitempty" yaml:"ca"`
	Depth            int      `json:"depth,omitempty" yaml:"depth"`
	SkipMtlsUriRegex []string `json:"skip_mtls_uri_regex,omitempty" yaml:"skip_mtls_uri_regex"`
}

// SSL ...
type SSL struct {
	ResourceMetadata `yaml:",inline"`
	Cert             string     `json:"cert,omitempty" yaml:"cert"`
	Key              string     `json:"key,omitempty" yaml:"key"`
	Sni              string     `json:"sni,omitempty" yaml:"sni"`
	Snis             []string   `json:"snis,omitempty" yaml:"snis"`
	Certs            []string   `json:"certs,omitempty" yaml:"certs"`
	Type             string     `json:"type,omitempty" yaml:"type"`
	Keys             []string   `json:"keys,omitempty" yaml:"keys"`
	ExpTime          int64      `json:"exptime,omitempty" yaml:"exptime"`
	Status           int        `json:"status" yaml:"status"`
	ValidityStart    int64      `json:"validity_start,omitempty" yaml:"validity_start"`
	ValidityEnd      int64      `json:"validity_end,omitempty" yaml:"validity_end"`
	Client           *SSLClient `json:"client,omitempty" yaml:"client"`
	SSLProtocols     []string   `json:"ssl_protocols,omitempty" yaml:"ssl_protocols"`
}

// Proto ...
type Proto struct {
	ResourceMetadata
	Desc    string `json:"desc,omitempty"`
	Content string `json:"content"`
}

// StreamRouteProtocol ...
type StreamRouteProtocol struct {
	Name string         `json:"name,omitempty"`
	Conf map[string]any `json:"conf,omitempty"`
}

// StreamRoute ...
type StreamRoute struct {
	ResourceMetadata
	RemoteAddr string               `json:"remote_addr,omitempty" yaml:"remote_addr"`
	ServerAddr string               `json:"server_addr,omitempty" yaml:"server_addr"`
	ServerPort int                  `json:"server_port,omitempty" yaml:"server_port"`
	SNI        string               `json:"sni,omitempty" yaml:"sni"`
	UpstreamID any                  `json:"upstream_id,omitempty" yaml:"upstream_id"`
	Upstream   *UpstreamDef         `json:"upstream,omitempty" yaml:"upstream"`
	ServiceID  any                  `json:"service_id,omitempty" yaml:"service_id"`
	Plugins    map[string]any       `json:"plugins,omitempty" yaml:"plugins"`
	Protocol   *StreamRouteProtocol `json:"protocol,omitempty" yaml:"protocol"`
}

// ResourceMetadata describes the metadata of a resource object, which includes the
// resource kind and name. It is used by the watch process of the ApigwEtcdWatcher type.
type ResourceMetadata struct {
	Labels        *LabelInfo              `json:"labels,omitempty" yaml:"labels"`
	APIVersion    string                  `json:"-" yaml:"-"`
	ID            string                  `json:"id,omitempty" yaml:"id"`
	Op            mvccpb.Event_EventType  `json:"-" yaml:"-"`
	Kind          constant.APISIXResource `json:"-" yaml:"-"`
	Name          string                  `json:"name,omitempty" yaml:"name"`
	RetryCount    int64                   `json:"-" yaml:"-"`
	Ctx           context.Context         `json:"-" yaml:"-"`
	ApisixVersion string                  `json:"apisix_version,omitempty" yaml:"apisix_version"`
}

// GetID returns the resource ID
func (rm *ResourceMetadata) GetID() string {
	return rm.ID
}

// GetGatewayName returns the gateway name from labels
func (rm *ResourceMetadata) GetGatewayName() string {
	if rm.Labels == nil {
		return ""
	}
	return rm.Labels.Gateway
}

// GetStageName returns the stage name from labels
func (rm *ResourceMetadata) GetStageName() string {
	if rm.Labels == nil {
		return ""
	}
	return rm.Labels.Stage
}

// GetStageKey returns the stage key from labels
func (rm *ResourceMetadata) GetStageKey() string {
	return config.GenStagePrimaryKey(rm.GetGatewayName(), rm.GetStageName())
}

// IsEmpty check if the metadata object is empty
func (rm *ResourceMetadata) IsEmpty() bool {
	if rm == nil {
		return true
	}
	// FIXME: there would be more global resources in the future, we need to add more, refactor this to a
	// IsGlobalKind function?
	// PluginMetadata 是全局资源，不依赖于 gateway 和 stage
	if rm.Kind == constant.PluginMetadata {
		return false
	}
	return rm.Labels.Gateway == "" && rm.Labels.Stage == ""
}

// IsGlobalResource check if the metadata object is global
func (rm *ResourceMetadata) IsGlobalResource() bool {
	// FIXME: there would be more global resources in the future, we need to add more, refactor this to a
	// IsGlobalKind function?
	return rm.Kind == constant.PluginMetadata && rm.GetStageName() == ""
}

// GetReleaseID returns the release ID for the resource
func (rm *ResourceMetadata) GetReleaseID() string {
	// stage 相关资源都是按照 stage 维度来管理的
	if rm.Kind != constant.PluginMetadata {
		return config.GenStagePrimaryKey(rm.Labels.Gateway, rm.Labels.Stage)
	}
	return rm.ID
}

// GetReleaseInfo returns the ReleaseInfo for the resource
func (rm *ResourceMetadata) GetReleaseInfo() *ReleaseInfo {
	return &ReleaseInfo{
		ResourceMetadata: *rm,
		PublishId:        cast.ToInt(rm.Labels.PublishId),
		ApisixVersion:    rm.Labels.ApisixVersion,
		Ctx:              rm.Ctx,
	}
}

// IsDeleteRelease checks if the resource is a delete release
func (rm *ResourceMetadata) IsDeleteRelease() bool {
	if rm.GetReleaseInfo() == nil {
		return false
	}
	// 判断是是否是删除发布
	return rm.GetReleaseInfo().Op == mvccpb.PUT &&
		cast.ToString(rm.GetReleaseInfo().PublishId) == constant.DeletePublishID
}

// ClearUnusedFields clears the unused fields for the resource
func (rm *ResourceMetadata) ClearUnusedFields() {
	if rm.Labels != nil {
		rm.Labels.PublishId = ""
	}
}

// GetCreateTime returns the create time for the resource
func (rm *ResourceMetadata) GetCreateTime() int64 {
	return 0
}

// GetUpdateTime returns the update time for the resource
func (rm *ResourceMetadata) GetUpdateTime() int64 {
	return 0
}

// SetCreateTime sets the create time for the resource
func (rm *ResourceMetadata) SetCreateTime(i int64) {
}

// SetUpdateTime sets the update time for the resource
func (rm *ResourceMetadata) SetUpdateTime(i int64) {
}

type ReleaseInfo struct {
	ResourceMetadata
	PublishId       int             `json:"publish_id,omitempty"`
	PublishTime     string          `json:"publish_time,omitempty"`
	ApisixVersion   string          `json:"apisix_version,omitempty"`
	ResourceVersion string          `json:"resource_version,omitempty"`
	Ctx             context.Context `json:"-"`
}

func (ri *ReleaseInfo) String() string {
	return fmt.Sprintf("%s:%d:%s:%s:%s",
		ri.ID, ri.PublishId, ri.PublishTime, ri.ApisixVersion, ri.ResourceVersion)
}

// IsNoNeedReport check if the release info is no need report
func (ri *ReleaseInfo) IsNoNeedReport() bool {
	publishID := cast.ToString(ri.PublishId)
	return publishID == constant.NoNeedReportPublishID || publishID == "" || publishID == constant.DeletePublishID
}

type LabelInfo struct {
	Gateway       string `json:"gateway.bk.tencent.com/gateway,omitempty"`
	Stage         string `json:"gateway.bk.tencent.com/stage,omitempty"`
	PublishId     string `json:"gateway.bk.tencent.com/publish-id,omitempty"`
	ApisixVersion string `json:"gateway.bk.tencent.com/apisix-version,omitempty"`
}
