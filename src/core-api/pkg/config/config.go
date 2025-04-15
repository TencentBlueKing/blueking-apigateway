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

package config

import (
	"errors"

	"github.com/spf13/viper"
)

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
}

// Logger is the config for all logger, including default logger and api
type Logger struct {
	Default LogConfig
	API     LogConfig
}

type TLS struct {
	Enabled     bool
	CertCaFile  string
	CertFile    string
	CertKeyFile string
	// for testing only, default false is secure; if set true will skip hostname verification, don't enable it in production
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

// Config is the config for the whole project
type Config struct {
	Debug bool

	Server Server
	Sentry Sentry

	Databases   []Database
	DatabaseMap map[string]Database

	Logger  Logger
	Tracing Tracing
}

// Load will load config from viper
func Load(v *viper.Viper) (*Config, error) {
	var cfg Config
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
	return &cfg, nil
}

// GinAPIEnabled get gin api trace switch
func (t Tracing) GinAPIEnabled() bool {
	return t.Enable && t.Instrument.GinAPI
}

// DBAPIEnabled get db api trace switch
func (t Tracing) DBAPIEnabled() bool {
	return t.Enable && t.Instrument.DbAPI
}
