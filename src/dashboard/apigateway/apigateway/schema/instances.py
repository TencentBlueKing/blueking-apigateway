# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
#     http://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.
#
# We undertake not to change the open source license (MIT license) applicable
# to the current version of the project delivered to anyone in the future.
#

# NOTE: schema instance is unchangeable after inserted into database

from django.utils import timezone

from apigateway.schema.constants import SchemaTypeEnum
from apigateway.schema.models import Schema
from apigateway.utils.singleton import Singleton

SCHEMA_NAME_CONTEXT_GATEWAY_BKAUTH = "ContextAPIBKAuth"
SCHEMA_NAME_CONTEXT_RESOURCE_BKAUTH = "ContextResourceBKAuth"
SCHEMA_NAME_CONTEXT_STAGE_PROXY_HTTP = "ContextStageProxyHTTP"
SCHEMA_NAME_CONTEXT_GATEWAY_FEATURE_FLAG = "ContextAPIFeatureFlag"
SCHEMA_NAME_PROXY_HTTP = "ProxyHTTP"
SCHEMA_NAME_PROXY_MOCK = "ProxyMock"
SCHEMA_NAME_MONITOR_ALARM_FILTER = "MonitorAlarmFilter"
SCHEMA_NAME_MONITOR_ALARM_STRATEGY = "MonitorAlarmStrategy"
SCHEMA_NAME_API_SDK = "APISDK"
SCHEMA_NAME_MICRO_GATEWAY = "MicroGateway"


class NewMetaSchemaMixin:
    name = ""
    type = ""
    schema = ""
    description = ""
    example = ""
    version = "1"

    def new_meta_schema(self) -> Schema:
        s = Schema()
        s.name = self.name
        s.type = self.type
        s.schema = self.schema
        s.description = self.description
        s.example = self.example
        s.version = self.version

        s.created_time = timezone.now()
        s.updated_time = timezone.now()

        return s


# =============== CONTEXT ===============
class ContextGatewayBKAuth(NewMetaSchemaMixin, metaclass=Singleton):
    version = "1"
    schema = """
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "api_type": {
      "type": "integer"
    },
    "unfiltered_sensitive_keys": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "user_auth_type": {
      "type": "string"
    },
    "uin_conf": {
      "type": "object",
      "properties": {
        "user_type": {
          "type": "string"
        },
        "from_uin_skey": {
          "type": "boolean"
        },
        "skey_type": {
          "type": "integer"
        },
        "domain_id": {
          "type": "integer"
        },
        "search_rtx": {
          "type": "boolean"
        },
        "search_rtx_source": {
          "type": "integer"
        },
        "from_openid": {
          "type": "boolean"
        },
        "from_auth_token": {
          "type": "boolean"
        }
      }
    },
    "rtx_conf": {
      "type": "object",
      "properties": {
        "user_type": {
          "type": "string"
        },
        "from_operator": {
          "type": "boolean"
        },
        "from_bk_ticket": {
          "type": "boolean"
        },
        "from_auth_token": {
          "type": "boolean"
        }
      }
    },
    "user_conf": {
      "type": "object",
      "properties": {
        "user_type": {
          "type": "string"
        },
        "from_bk_token": {
          "type": "boolean"
        },
        "from_username": {
          "type": "boolean"
        }
      }
    }
  }
}
    """
    example = """
{
    "api_type": 0,
    "unfiltered_sensitive_keys": ["a", "b"],
    "user_auth_type": "tencent",
    "uin_conf": {
            "user_type": "uin",
            "from_uin_skey": true,
            "skey_type": 0,
            "domain_id": 389,
            "search_rtx": true,
            "search_rtx_source": 0,
            "from_openid": true,
            "from_auth_token": true,
    },
    "rtx_conf": {
            "user_type": "rtx",
            "from_operator": true,
            "from_bk_ticket": true,
            "from_auth_token": true,
    },
    "user_conf": {
            "user_type": "default",
            "from_bk_token": true,
            "from_username": false
    }
}
    """
    name = SCHEMA_NAME_CONTEXT_GATEWAY_BKAUTH
    type = SchemaTypeEnum.CONTEXT.value
    description = "Gateway auth property schema"


class ContextResourceBKAuth(NewMetaSchemaMixin, metaclass=Singleton):
    version = "1"
    schema = """
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "skip_auth_verification",
    "auth_verified_required",
    "app_verified_required",
    "resource_perm_required"
  ],
  "properties": {
    "skip_auth_verification": {
      "type": "boolean"
    },
    "auth_verified_required": {
      "type": "boolean"
    },
    "app_verified_required": {
      "type": "boolean"
    },
    "resource_perm_required": {
      "type": "boolean"
    }
  }
}
    """
    example = """
{
  "skip_auth_verification": false,
  "auth_verified_required": false,
  "app_verified_required": true,
  "resource_perm_required": true
}
    """
    name = SCHEMA_NAME_CONTEXT_RESOURCE_BKAUTH
    type = SchemaTypeEnum.CONTEXT.value
    description = "BKAuth Middleware"


class ContextStageProxyHTTP(NewMetaSchemaMixin, metaclass=Singleton):
    version = "1"
    schema = """
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "timeout",
    "upstreams",
    "transform_headers"
  ],
  "properties": {
    "timeout": {
      "type": "integer",
      "minimum": 0
    },
    "upstreams": {
      "type": "object",
      "required": [
        "loadbalance",
        "hosts"
      ],
      "properties": {
        "loadbalance": {
          "type": "string"
        },
        "hosts": {
          "type": "array",
          "items": {
            "type": "object"
          }
        }
      }
    },
    "transform_headers": {
      "delete": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "add": {
        "type": "object",
        "additionalProperties": {
          "type": "string"
        }
      },
      "append": {
        "type": "object",
        "additionalProperties": {
          "type": "string"
        }
      },
      "replace": {
        "type": "object",
        "additionalProperties": {
          "type": "string"
        }
      },
      "set": {
        "type": "object",
        "additionalProperties": {
          "type": "string"
        }
      }
    }
  }
}
    """
    example = """
{
  "timeout": 10,
  "upstreams": {
    "loadbalance": "roundrobin",
    "hosts": [
      {
        "host": "www.a.com",
        "weight": 50,
      },
      {
        "host": "www.b.com",
        "weight": 50,
      }
    ]
  },
  "transform_headers": {
      "add": {"k1": "v1", "k2": "v2"},
      "append": {"k1": "v1", "k2": "v2"},
      "replace": {"k1": "v1", "k2": "v2"},
      "set": {"k1": "v1", "k2": "v2"},
      "delete": ["k3", "k4"],
  }
}
    """
    name = SCHEMA_NAME_CONTEXT_STAGE_PROXY_HTTP
    type = SchemaTypeEnum.CONTEXT.value
    description = "HTTP proxy schema"


class ContextGatewayFeatureFlag(NewMetaSchemaMixin, metaclass=Singleton):
    version = "1"
    schema = """
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "additionalProperties": false,
  "patternProperties": {
    "^[A-Z0-9_-]+$": {
      "type": "boolean"
    }
  }
}
    """
    example = """{"MY_FEATURE": true}"""
    name = SCHEMA_NAME_CONTEXT_GATEWAY_FEATURE_FLAG
    type = SchemaTypeEnum.CONTEXT.value
    description = "Gateway feature flags"


# =============== PROXY ===============
class ProxyHTTP(NewMetaSchemaMixin, metaclass=Singleton):
    version = "1"
    schema = """
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "method",
    "path"
  ],
  "properties": {
    "method": {
      "type": "string"
    },
    "path": {
      "type": "string"
    },
    "match_subpath": {
      "type": "boolean"
    },
    "transform_headers": {
      "delete": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "add": {
        "type": "object",
        "additionalProperties": {
          "type": "string"
        }
      },
      "append": {
        "type": "object",
        "additionalProperties": {
          "type": "string"
        }
      },
      "replace": {
        "type": "object",
        "additionalProperties": {
          "type": "string"
        }
      },
      "set": {
        "type": "object",
        "additionalProperties": {
          "type": "string"
        }
      }
    }
  }
}
    """

    example = """
{
  "method": "GET",
  "path": "/echo/",
  "transform_headers": {
      "add": {"k1": "v1", "k2": "v2"},
      "append": {"k1": "v1", "k2": "v2"},
      "replace": {"k1": "v1", "k2": "v2"},
      "set": {"k1": "v1", "k2": "v2"},
      "delete": ["k3", "k4"],
  }
}
    """
    name = SCHEMA_NAME_PROXY_HTTP
    type = SchemaTypeEnum.PROXY.value
    description = "HTTP proxy schema"


class ProxyMock(NewMetaSchemaMixin, metaclass=Singleton):
    version = "1"
    schema = """
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "code",
    "body",
    "headers"
  ],
  "properties": {
    "code": {
      "type": "integer",
      "minimum": 0
    },
    "body": {
      "type": "string"
    },
    "headers": {
      "type": "object"
    }
  }
}
    """
    example = """
{
    "code": 200,
    "body": "test",
    "headers": {
        "X-API-HELLO": "world"
    }
}
    """
    name = SCHEMA_NAME_PROXY_MOCK
    type = SchemaTypeEnum.PROXY.value
    description = "Mock proxy schema"


class MonitorAlarmFilter(NewMetaSchemaMixin, metaclass=Singleton):
    version = "1"
    schema = """
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "field": {
        "type": "string"
      },
      "method": {
        "type": "string"
      },
      "value": {
        "anyOf": [
          {
            "type": "integer"
          },
          {
            "type": "string"
          },
          {
            "type": "array",
            "items": {
              "type": "string"
            }
          }
        ]
      }
    }
  }
}
    """
    example = """
[{"field": "status", "method": "eq", "value": 400}]
    """
    name = SCHEMA_NAME_MONITOR_ALARM_FILTER
    type = SchemaTypeEnum.MONITOR.value
    description = "monitor alarm filter schema"


class MonitorAlarmStrategy(NewMetaSchemaMixin, metaclass=Singleton):
    version = "1"
    schema = """
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "detect_config",
    "converge_config",
    "notice_config"
  ],
  "properties": {
    "detect_config": {
      "type": "object",
      "required": [
        "duration",
        "method",
        "count"
      ],
      "properties": {
        "duration": {
          "type": "integer",
          "minimum": 0
        },
        "method": {
          "type": "string"
        },
        "count": {
          "type": "integer",
          "minimum": 0
        }
      }
    },
    "converge_config": {
      "type": "object",
      "required": [
        "duration"
      ],
      "properties": {
        "duration": {
          "type": "integer",
          "minimum": 0
        }
      }
    },
    "notice_config": {
      "type": "object",
      "required": [
        "notice_way",
        "notice_role",
        "notice_extra_receiver"
      ],
      "properties": {
        "notice_way": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "notice_role": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "notice_extra_receiver": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      }
    }
  }
}
    """
    example = """
{
  "detect_config": {
    "duration": 300,
    "method": "gte",
    "count": 10
  },
  "converge_config": {
    "duration": 300
  },
  "notice_config": {
    "notice_way": [
      "wechat",
      "wechat-work"
    ],
    "notice_role": [
      "creator",
      "maintainer"
    ],
    "notice_extra_receiver": [
      "admin"
    ]
  }
}
    """
    name = SCHEMA_NAME_MONITOR_ALARM_STRATEGY
    type = SchemaTypeEnum.MONITOR.value
    description = "monitor alarm strategy schema"


class APISDK(NewMetaSchemaMixin, metaclass=Singleton):
    version = "1"
    schema = """
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "python": {
      "type": "object",
      "required": [
        "is_uploaded_to_pypi"
      ],
      "properties": {
        "is_uploaded_to_pypi": {
          "type": "boolean"
        }
      }
    }
  }
}
    """
    example = """
{
    "python": {
        "is_uploaded_to_pypi": true
    }
}
    """
    name = SCHEMA_NAME_API_SDK
    type = SchemaTypeEnum.APISDK.value
    description = "api sdk"


class MicroGateway(NewMetaSchemaMixin, metaclass=Singleton):
    version = "1"
    schema = """
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["jwt_auth", "http"],
  "properties": {
    "metadata": {
      "type": "object",
      "properties": {
        "is_managed": {
          "type": "boolean"
        }
      }
    },
    "bcs": {
      "type": "object",
      "properties": {
        "project_name": {
          "type": "string"
        },
        "project_id": {
          "type": "string"
        },
        "cluster_id": {
          "type": "string"
        },
        "namespace": {
          "type": "string"
        },
        "chart_name": {
          "type": "string"
        },
        "chart_version": {
          "type": "string"
        },
        "release_name": {
          "type": "string"
        }
      }
    },
    "jwt_auth": {
      "type": "object",
      "required": ["secret_key"],
      "properties": {
        "secret_key": {
          "type": "string"
        }
      }
    },
    "http": {
      "type": "object",
      "required": ["http_url"],
      "properties": {
        "http_url": {
          "type": "string"
        }
      }
    },
    "values": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
    """
    example = """
{
    "bcs": {
        "project_name": "demo",
        "project_id": "demo",
        "cluster_id": "demo",
        "namespace": "default",
        "chart_name": "bk-micro-gateway",
        "chart_version": "1.0.0",
        "release_name": "demo-v1"
    },
    "jwt_auth": {
      "secret_key": "my-secret"
    },
    "http": {
      "http_url": "http://demo.example.com"
    }
}
    """
    name = SCHEMA_NAME_MICRO_GATEWAY
    type = SchemaTypeEnum.MICRO_GATEWAY.value
    description = "micro gateway"
