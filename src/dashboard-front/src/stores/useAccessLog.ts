import { defineStore } from 'pinia';

import { t } from '@/locales';

export const useAccessLog = defineStore('useAccessLog', {
  state: () => ({
    // 日期选择快捷方式
    datepickerShortcuts: [
      {
        text: t('最近5分钟'),
        value() {
          const end = new Date();
          const start = new Date();
          start.setTime(start.getTime() - 5 * 60 * 1000);
          return [start, end];
        },
      },
      {
        text: t('最近1小时'),
        value() {
          const end = new Date();
          const start = new Date();
          start.setTime(start.getTime() - 60 * 60 * 1000);
          return [start, end];
        },
      },
      {
        text: t('最近6小时'),
        value() {
          const end = new Date();
          const start = new Date();
          start.setTime(start.getTime() - 6 * 60 * 60 * 1000);
          return [start, end];
        },
      },
      {
        text: t('最近12小时'),
        value() {
          const end = new Date();
          const start = new Date();
          start.setTime(start.getTime() - 12 * 60 * 60 * 1000);
          return [start, end];
        },
      },
      {
        text: t('最近1天'),
        value() {
          const end = new Date();
          const start = new Date();
          start.setTime(start.getTime() - 24 * 60 * 60 * 1000);
          return [start, end];
        },
      },
      {
        text: t('最近7天'),
        value() {
          const end = new Date();
          const start = new Date();
          start.setTime(start.getTime() - 3600 * 1000 * 24 * 7);
          return [start, end];
        },
      },
    ],
    // 业务组件-时间选择器的常用列表
    commonUseList: [
      {
        name: t('近 5 分钟'),
        id: ['now-5m', 'now'],
      },
      {
        name: t('近 15 分钟'),
        id: ['now-15m', 'now'],
      },
      {
        name: t('近 30 分钟'),
        id: ['now-30m', 'now'],
      },
      {
        name: t('近 1 小时'),
        id: ['now-1h', 'now'],
      },
      {
        name: t('近 6 小时'),
        id: ['now-6h', 'now'],
      },
      {
        name: t('近 12 小时'),
        id: ['now-12h', 'now'],
      },
      {
        name: t('近 24 小时'),
        id: ['now-24h', 'now'],
      },
      {
        name: t('近 7 天'),
        id: ['now-7d', 'now'],
      },
      {
        name: t('近 30 天'),
        id: ['now-30d', 'now'],
      },
      {
        name: t('近 180 天'),
        id: ['now-180d', 'now'],
      },
      {
        name: t('今天'),
        id: ['now/d', 'now/d'],
      },
      {
        name: t('今天（至今）'),
        id: ['now/d', 'now'],
      },
      {
        name: t('昨天'),
        id: ['now-1d/d', 'now-1d/d'],
      },
      {
        name: t('前天'),
        id: ['now-2d/d', 'now-2d/d'],
      },
      {
        name: t('本周'),
        id: ['now/w', 'now/w'],
      },
      {
        name: t('本周（至今）'),
        id: ['now/w', 'now'],
      },
      {
        name: t('上周'),
        id: ['now-1w/w', 'now-1w/w'],
      },
      {
        name: t('本月'),
        id: ['now/M', 'now/M'],
      },
      {
        name: t('本月（至今）'),
        id: ['now/M', 'now'],
      },
      {
        name: t('上月'),
        id: ['now-1M/M', 'now-1M/M'],
      },
      {
        name: t('上月（至今）'),
        id: ['now-1M/M', 'now'],
      },
    ],
    // 一天内的快捷方式
    shortcutsInDay: [
      {
        text: t('最近5分钟'),
        value() {
          const end = new Date();
          const start = new Date();
          start.setTime(start.getTime() - 5 * 60 * 1000);
          return [start, end];
        },
      },
      {
        text: t('最近1小时'),
        value() {
          const end = new Date();
          const start = new Date();
          start.setTime(start.getTime() - 60 * 60 * 1000);
          return [start, end];
        },
      },
      {
        text: t('最近6小时'),
        value() {
          const end = new Date();
          const start = new Date();
          start.setTime(start.getTime() - 6 * 60 * 60 * 1000);
          return [start, end];
        },
      },
      {
        text: t('最近12小时'),
        value() {
          const end = new Date();
          const start = new Date();
          start.setTime(start.getTime() - 12 * 60 * 60 * 1000);
          return [start, end];
        },
      },
      {
        text: t('最近1天'),
        value() {
          const end = new Date();
          const start = new Date();
          start.setTime(start.getTime() - 24 * 60 * 60 * 1000);
          return [start, end];
        },
      },
    ],
    // 告警策略选项
    alarmStrategyOptions: {
      alarmType: [
        {
          name: t('API Gateway 请求后端错误'),
          value: 'resource_backend',
        },
      ],
      alarmSubType: [
        {
          name: t('后端响应状态码5xx'),
          value: 'status_code_5xx',
        },
        {
          name: t('请求后端响应超时'),
          value: 'gateway_timeout',
        },
        {
          name: t('请求后端502错误'),
          value: 'bad_gateway',
        },
      ],
      detectConfig: {
        duration: [
          {
            name: t('5分钟'),
            value: 5 * 60,
          },
          {
            name: t('10分钟'),
            value: 10 * 60,
          },
          {
            name: t('30分钟'),
            value: 30 * 60,
          },
          {
            name: t('60分钟'),
            value: 60 * 60,
          },
        ],
        method: [
          {
            name: '>',
            value: 'gt',
          },
          {
            name: '>=',
            value: 'gte',
          },
          {
            name: '<',
            value: 'lt',
          },
          {
            name: '<=',
            value: 'lte',
          },
          {
            name: '=',
            value: 'eq',
          },
        ],
      },
      convergeConfig: {
        duration: [
          {
            name: t('24小时'),
            value: 1440 * 60,
          },
          {
            name: t('12小时'),
            value: 720 * 60,
          },
          {
            name: t('6小时'),
            value: 360 * 60,
          },
          {
            name: t('1小时'),
            value: 60 * 60,
          },
          {
            name: t('30分钟'),
            value: 30 * 60,
          },
          {
            name: t('15分钟'),
            value: 15 * 60,
          },
          {
            name: t('5分钟'),
            value: 5 * 60,
          },
          {
            name: t('0分钟'),
            value: 0,
          },
        ],
      },
    },
    // 告警状态
    alarmStatus: [
      {
        name: t('已接收'),
        value: 'received',
      },
      {
        name: t('已忽略'),
        value: 'skipped',
      },
      {
        name: t('告警成功'),
        value: 'success',
      },
      {
        name: t('告警失败'),
        value: 'failure',
      },
    ],
    // 请求方法列表
    methodList: [
      {
        id: 'GET',
        name: 'GET',
      },
      {
        id: 'POST',
        name: 'POST',
      },
      {
        id: 'PUT',
        name: 'PUT',
      },
      {
        id: 'PATCH',
        name: 'PATCH',
      },
      {
        id: 'DELETE',
        name: 'DELETE',
      },

      {
        id: 'HEAD',
        name: 'HEAD',
      },
      {
        id: 'OPTIONS',
        name: 'OPTIONS',
      },
      {
        id: 'ANY',
        name: 'ANY',
      },
    ],
    // SDK 语言列表
    SDKLanguageList: [
      {
        name: 'python',
        value: 'python',
      },
      {
        name: 'golang',
        value: 'golang',
      },
    ],
    // 审计选项
    auditOptions: {
      OPObjectType: [
        {
          name: t('网关'),
          value: 'gateway',
        },
        {
          name: t('环境'),
          value: 'stage',
        },
        {
          name: t('资源'),
          value: 'resource',
        },
        {
          name: t('资源文档'),
          value: 'resource_doc',
        },
        {
          name: t('资源版本'),
          value: 'resource_version',
        },
        {
          name: t('发布'),
          value: 'release',
        },
        // {
        //   name: t('策略'),
        //   value: 'access_strategy',
        // },
        // {
        //   name: t('IP分组'),
        //   value: 'ip_group',
        // },
        {
          name: t('标签'),
          value: 'gateway_label',
        },
        {
          name: t('插件'),
          value: 'plugin',
        },
        {
          name: t('后端服务'),
          value: 'backend',
        },
        {
          name: 'MCP Server',
          value: 'mcp_server',
        },
      ],
      OPType: [
        {
          name: t('创建'),
          value: 'create',
        },
        {
          name: t('修改'),
          value: 'modify',
        },
        {
          name: t('删除'),
          value: 'delete',
        },
      ],
    },
  }),
  getters: {
    /**
     * 获取日期选择快捷方式
     * @param {Object} state - store 的状态对象
     * @returns {Array} 日期选择快捷方式数组
     */
    getDatepickerShortcuts(state) {
      return state.datepickerShortcuts;
    },
    /**
     * 获取一天内的快捷方式
     * @param {Object} state - store 的状态对象
     * @returns {Array} 一天内的快捷方式数组
     */
    getShortcutsInDay(state) {
      return state.shortcutsInDay;
    },
    /**
     * 获取告警策略选项
     * @param {Object} state - store 的状态对象
     * @returns {Object} 告警策略选项对象
     */
    getAlarmStrategyOptions(state) {
      return state.alarmStrategyOptions;
    },
    /**
     * 获取告警状态
     * @param {Object} state - store 的状态对象
     * @returns {Array} 告警状态数组
     */
    getAlarmStatus(state) {
      return state.alarmStatus;
    },
    /**
     * 获取请求方法列表
     * @param {Object} state - store 的状态对象
     * @returns {Array} 请求方法列表数组
     */
    getMethodList(state) {
      return state.methodList;
    },
    /**
     * 获取 SDK 语言列表
     * @param {Object} state - store 的状态对象
     * @returns {Array} SDK 语言列表数组
     */
    getSDKLanguageList(state) {
      return state.SDKLanguageList;
    },
    /**
     * 获取审计选项
     * @param {Object} state - store 的状态对象
     * @returns {Object} 审计选项对象
     */
    getAuditOptions(state) {
      return state.auditOptions;
    },
  },
});
