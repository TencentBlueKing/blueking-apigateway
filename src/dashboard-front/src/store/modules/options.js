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
/**
 * @file app store
 * @author
 */
import i18n from '@/language/i18n.js'

export default {
  namespaced: true,
  state: {
    datepickerShortcuts: [
      {
        text: i18n.t('最近5分钟'),
        value () {
          const end = new Date()
          const start = new Date()
          start.setTime(start.getTime() - 5 * 60 * 1000)
          return [start, end]
        }
      },
      {
        text: i18n.t('最近1小时'),
        value () {
          const end = new Date()
          const start = new Date()
          start.setTime(start.getTime() - 60 * 60 * 1000)
          return [start, end]
        }
      },
      {
        text: i18n.t('最近6小时'),
        value () {
          const end = new Date()
          const start = new Date()
          start.setTime(start.getTime() - 6 * 60 * 60 * 1000)
          return [start, end]
        }
      },
      {
        text: i18n.t('最近12小时'),
        value () {
          const end = new Date()
          const start = new Date()
          start.setTime(start.getTime() - 12 * 60 * 60 * 1000)
          return [start, end]
        }
      },
      {
        text: i18n.t('最近1天'),
        value () {
          const end = new Date()
          const start = new Date()
          start.setTime(start.getTime() - 24 * 60 * 60 * 1000)
          return [start, end]
        }
      },
      {
        text: i18n.t('最近7天'),
        value () {
          const end = new Date()
          const start = new Date()
          start.setTime(start.getTime() - 3600 * 1000 * 24 * 7)
          return [start, end]
        }
      }
    ],
    shortcutsInDay: [
      {
        text: i18n.t('最近5分钟'),
        value () {
          const end = new Date()
          const start = new Date()
          start.setTime(start.getTime() - 5 * 60 * 1000)
          return [start, end]
        }
      },
      {
        text: i18n.t('最近1小时'),
        value () {
          const end = new Date()
          const start = new Date()
          start.setTime(start.getTime() - 60 * 60 * 1000)
          return [start, end]
        }
      },
      {
        text: i18n.t('最近6小时'),
        value () {
          const end = new Date()
          const start = new Date()
          start.setTime(start.getTime() - 6 * 60 * 60 * 1000)
          return [start, end]
        }
      },
      {
        text: i18n.t('最近12小时'),
        value () {
          const end = new Date()
          const start = new Date()
          start.setTime(start.getTime() - 12 * 60 * 60 * 1000)
          return [start, end]
        }
      },
      {
        text: i18n.t('最近1天'),
        value () {
          const end = new Date()
          const start = new Date()
          start.setTime(start.getTime() - 24 * 60 * 60 * 1000)
          return [start, end]
        }
      }
    ],
    alarmStrategyOptions: {
      alarmType: [
        {
          name: i18n.t('API Gateway 请求后端错误'),
          value: 'resource_backend'
        }
      ],
      alarmSubType: [
        {
          name: i18n.t('后端响应状态码5xx'),
          value: 'status_code_5xx'
        },
        {
          name: i18n.t('请求后端响应超时'),
          value: 'gateway_timeout'
        },
        {
          name: i18n.t('请求后端502错误'),
          value: 'bad_gateway'
        }
      ],
      detectConfig: {
        duration: [
          {
            name: i18n.t('5分钟'),
            value: 5 * 60
          },
          {
            name: i18n.t('10分钟'),
            value: 10 * 60
          },
          {
            name: i18n.t('30分钟'),
            value: 30 * 60
          },
          {
            name: i18n.t('60分钟'),
            value: 60 * 60
          }
        ],
        method: [
          {
            name: '>',
            value: 'gt'
          },
          {
            name: '>=',
            value: 'gte'
          },
          {
            name: '<',
            value: 'lt'
          },
          {
            name: '<=',
            value: 'lte'
          },
          {
            name: '=',
            value: 'eq'
          }
        ]
      },
      convergeConfig: {
        duration: [
          {
            name: i18n.t('24小时'),
            value: 1440 * 60
          },
          {
            name: i18n.t('12小时'),
            value: 720 * 60
          },
          {
            name: i18n.t('6小时'),
            value: 360 * 60
          },
          {
            name: i18n.t('1小时'),
            value: 60 * 60
          },
          {
            name: i18n.t('30分钟'),
            value: 30 * 60
          },
          {
            name: i18n.t('15分钟'),
            value: 15 * 60
          },
          {
            name: i18n.t('5分钟'),
            value: 5 * 60
          },
          {
            name: i18n.t('0分钟'),
            value: 0
          }
        ]
      }
    },
    alarmStatus: [
      {
        name: i18n.t('已接收'),
        value: 'received'
      },
      {
        name: i18n.t('已忽略'),
        value: 'skipped'
      },
      {
        name: i18n.t('告警成功'),
        value: 'success'
      },
      {
        name: i18n.t('告警失败'),
        value: 'failure'
      }
    ],
    methodList: [
      {
        id: 'GET',
        name: 'GET'
      },
      {
        id: 'POST',
        name: 'POST'
      },
      {
        id: 'PUT',
        name: 'PUT'
      },
      {
        id: 'PATCH',
        name: 'PATCH'
      },
      {
        id: 'DELETE',
        name: 'DELETE'
      },

      {
        id: 'HEAD',
        name: 'HEAD'
      },
      {
        id: 'OPTIONS',
        name: 'OPTIONS'
      },
      {
        id: 'ANY',
        name: 'ANY'
      }
    ],
    SDKLanguageList: [
      {
        name: 'python',
        value: 'python'
      },
      {
        name: 'golang',
        value: 'golang'
      }
    ],
    auditOptions: {
      OPObjectType: [
        {
          name: i18n.t('网关'),
          value: 'api'
        },
        {
          name: i18n.t('环境'),
          value: 'stage'
        },
        {
          name: i18n.t('资源'),
          value: 'resource'
        },
        {
          name: i18n.t('版本'),
          value: 'resource_version'
        },
        {
          name: i18n.t('发布'),
          value: 'release'
        },
        {
          name: i18n.t('策略'),
          value: 'access_strategy'
        },
        {
          name: i18n.t('IP分组'),
          value: 'ip_group'
        },
        {
          name: i18n.t('标签'),
          value: 'api_label'
        },
        {
          name: i18n.t('插件'),
          value: 'plugin'
        }
      ],
      OPType: [
        {
          name: i18n.t('创建'),
          value: 'create'
        },
        {
          name: i18n.t('修改'),
          value: 'modify'
        },
        {
          name: i18n.t('删除'),
          value: 'delete'
        }
      ]
    }
  },
  getters: {
    getOptionByKey: state => key => {
      return state[key]
    },
    datepickerShortcuts: state => state.datepickerShortcuts,
    shortcutsInDay: state => state.shortcutsInDay,
    alarmStrategyOptions: state => state.alarmStrategyOptions,
    alarmStatus: state => state.alarmStatus,
    methodList: state => state.methodList,
    SDKLanguageList: state => state.SDKLanguageList,
    auditOptions: state => state.auditOptions
  },
  mutations: {
  },
  actions: {
  }
}
