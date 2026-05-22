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

import (
	"errors"
	"net"
	"strconv"
	"strings"

	"github.com/apache/apisix-ingress-controller/pkg/log"
)

func mapKV2Node(key string, val float64) (*Node, error) {
	host, port, err := net.SplitHostPort(key)

	// ipv6 address
	if strings.Count(host, ":") >= 2 {
		host = "[" + host + "]"
	}

	if err != nil {
		if strings.Contains(err.Error(), "missing port in address") {
			//  according to APISIX upstream nodes policy, port is optional
			host = key
			port = "0"
		} else {
			return nil, errors.New("invalid upstream node")
		}
	}

	portInt, err := strconv.Atoi(port)
	if err != nil {
		log.Errorf("parse port to int fail: %s", err)
		return nil, err
	}

	node := &Node{
		Host:   host,
		Port:   portInt,
		Weight: int(val),
	}

	return node, nil
}

// NodesFormat convert obj to []*Node
func NodesFormat(obj any) any {
	nodes := make([]*Node, 0)
	switch value := obj.(type) {
	case map[string]float64:
		log.Infof("nodes type: %v", value)
		for key, val := range value {
			node, err := mapKV2Node(key, val)
			if err != nil {
				return obj
			}
			nodes = append(nodes, node)
		}
		return nodes
	case map[string]any:
		log.Infof("nodes type: %v", value)
		for key, val := range value {
			fval, ok := val.(float64)
			if !ok {
				return obj
			}
			node, err := mapKV2Node(key, fval)
			if err != nil {
				return obj
			}
			nodes = append(nodes, node)
		}
		return nodes
	case []*Node:
		log.Infof("nodes type: %v", value)
		return obj
	case []any:
		log.Infof("nodes type []interface{}: %v", value)
		for _, v := range value {
			val, ok := v.(map[string]any)
			if !ok {
				return obj
			}
			host, _ := val["host"].(string)
			portF, _ := val["port"].(float64)
			weightF, _ := val["weight"].(float64)
			node := &Node{
				Host:   host,
				Port:   int(portF),
				Weight: int(weightF),
			}
			if p, ok := val["priority"].(float64); ok {
				node.Priority = int(p)
			}
			if m, ok := val["metadata"].(map[string]any); ok {
				node.Metadata = m
			}

			nodes = append(nodes, node)
		}
		return nodes
	}

	return obj
}
