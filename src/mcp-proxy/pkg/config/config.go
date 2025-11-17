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

// Package config is the config for the whole project
package config

import (
	"errors"
	"fmt"
	"os"
	"time"

	"github.com/spf13/viper"
)

// G ...
var G *Config

// Server is the config for http server
type Server struct {
	Host string
	Port int

	GraceTimeout int64

	ReadTimeout  int
	WriteTimeout int
	IdleTimeout  int
}

// LogConfig is the detail config for a logger
type LogConfig struct {
	Level    string
	Writer   string
	Settings map[string]string
	Buffered bool
	// 日志脱敏
	Desensitization DesensitizationConfig
}

// DesensitizationConfig ...
type DesensitizationConfig struct {
	// 脱敏日志开关
	Enabled bool
	// 敏感字段列表
	Fields []DesensitizationFiled
}

// DesensitizationFiled ...
type DesensitizationFiled struct {
	// 敏感字段所属的 filed key
	Key string
	// 敏感字段 JsonPath
	JsonPath []string
}

// Logger is the config for all logger, including default logger and api
type Logger struct {
	Default LogConfig
	API     LogConfig
	Audit   LogConfig
}

// TLS is the config for tls
type TLS struct {
	Enabled     bool
	CertCaFile  string
	CertFile    string
	CertKeyFile string
	// for testing only, default false is secure;
	// if set true will skip hostname verification, don't enable it in production
	InsecureSkipVerify bool
}

// Database is the config for database connection
type Database struct {
	ID       string
	Host     string
	Port     int
	User     string
	Password string
	Name     string

	MaxOpenConns          int
	MaxIdleConns          int
	ConnMaxLifetimeSecond int
	// connect: s
	Timeout int
	// tls
	TLS TLS
}

// DSN ...
func (d *Database) DSN() string {
	dsn := fmt.Sprintf(
		"%s:%s@tcp(%s:%d)/%s?parseTime=true",
		d.User,
		d.Password,
		d.Host,
		d.Port,
		d.Name,
	)
	// 添加TLS配置参数
	if d.TLS.Enabled {
		dsn = fmt.Sprintf("%s&tls=%s", dsn, d.TLSCfgName())
	}

	return dsn
}

// TLSCfgName mysql tls 配置名称
func (d *Database) TLSCfgName() string {
	return "custom"
}

// Sentry is the config for sentry
type Sentry struct {
	DSN            string
	ReportLogLevel int
}

// Tracing is the config for trace
type Tracing struct {
	Enable       bool
	Endpoint     string
	Type         string
	Token        string
	Sampler      string
	SamplerRatio float64
	ServiceName  string
	Instrument   Instrument
}

// Instrument  is the config for trace
type Instrument struct {
	GinAPI bool
	DbAPI  bool
}

// McpServer ...
type McpServer struct {
	// the interval of mcp server reload
	Interval                    time.Duration
	BkApiUrlTmpl                string
	MessageUrlFormat            string
	MessageApplicationUrlFormat string
	InnerJwtExpireTime          time.Duration
	EncryptKey                  string
	CryptoNonce                 string
}

// PProf is the config for pprof
type PProf struct {
	Username string
	Password string
}

// Config is the config for the whole project
type Config struct {
	Debug bool

	Server Server
	Sentry Sentry

	Databases   []Database
	DatabaseMap map[string]Database

	Logger  Logger
	Tracing Tracing

	McpServer McpServer
	PProf     PProf
}

// Load will load config from viper
func Load(v *viper.Viper) (*Config, error) {
	var cfg *Config
	// 将配置信息绑定到结构体上
	if err := v.Unmarshal(&cfg); err != nil {
		return nil, err
	}

	// parse the list to map
	// 1. database
	cfg.DatabaseMap = make(map[string]Database)
	for _, db := range cfg.Databases {
		cfg.DatabaseMap[db.ID] = db
	}

	if len(cfg.DatabaseMap) == 0 {
		return nil, errors.New("database cannot be empty")
	}

	// 验证所有数据库配置
	for _, db := range cfg.Databases {
		if err := db.ValidateDatabase(); err != nil {
			return nil, err
		}
	}

	if cfg.McpServer.Interval == 0 {
		cfg.McpServer.Interval = 60 * time.Second
	}
	if cfg.McpServer.BkApiUrlTmpl == "" {
		cfg.McpServer.BkApiUrlTmpl = os.Getenv("BK_API_URL_TMPL")
	}
	if cfg.McpServer.MessageUrlFormat == "" {
		cfg.McpServer.MessageUrlFormat = "/api/bk-apigateway/prod/api/v2/mcp-servers/%s/sse/message"
	}
	// mcp 应用态的url消息地址
	if cfg.McpServer.MessageApplicationUrlFormat == "" {
		cfg.McpServer.MessageApplicationUrlFormat = "/api/bk-apigateway/prod/api/v2/mcp-servers/%s/application/sse/message"
	}
	if cfg.McpServer.InnerJwtExpireTime == 0 {
		cfg.McpServer.InnerJwtExpireTime = time.Minute * 5
	}
	if cfg.McpServer.EncryptKey == "" {
		cfg.McpServer.EncryptKey = os.Getenv("ENCRYPT_KEY")
	}
	if cfg.McpServer.CryptoNonce == "" {
		cfg.McpServer.CryptoNonce = os.Getenv("BK_APIGW_CRYPTO_NONCE")
	}

	if cfg.PProf.Username == "" {
		cfg.PProf.Username = os.Getenv("PPROF_USERNAME")
		if cfg.PProf.Username == "" {
			cfg.PProf.Username = "admin" // 默认用户名
		}
	}
	if cfg.PProf.Password == "" {
		cfg.PProf.Password = os.Getenv("PPROF_PASSWORD")
		if cfg.PProf.Password == "" {
			cfg.PProf.Password = "admin" // 默认密码，生产环境应该修改
		}
	}

	G = cfg
	return cfg, nil
}

// GinAPIEnabled get gin api trace switch
func (t Tracing) GinAPIEnabled() bool {
	return t.Enable && t.Instrument.GinAPI
}

// DBAPIEnabled get db api trace switch
func (t Tracing) DBAPIEnabled() bool {
	return t.Enable && t.Instrument.DbAPI
}

// ValidateTLS 验证TLS配置
func (t TLS) ValidateTLS() error {
	if !t.Enabled {
		return nil
	}

	// 如果启用了TLS，检查证书文件是否存在
	if t.CertCaFile != "" {
		if _, err := os.Stat(t.CertCaFile); os.IsNotExist(err) {
			return fmt.Errorf("TLS CA certificate file not found: %s", t.CertCaFile)
		}
	}

	if t.CertFile != "" {
		if _, err := os.Stat(t.CertFile); os.IsNotExist(err) {
			return fmt.Errorf("TLS certificate file not found: %s", t.CertFile)
		}
	}

	if t.CertKeyFile != "" {
		if _, err := os.Stat(t.CertKeyFile); os.IsNotExist(err) {
			return fmt.Errorf("TLS private key file not found: %s", t.CertKeyFile)
		}
	}

	return nil
}

// ValidateDatabase 验证数据库配置
func (d Database) ValidateDatabase() error {
	// 验证TLS配置
	if err := d.TLS.ValidateTLS(); err != nil {
		return fmt.Errorf("database %s TLS config validation failed: %w", d.ID, err)
	}

	return nil
}
