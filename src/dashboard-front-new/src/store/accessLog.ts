import { defineStore } from 'pinia';
import i18n from '@/language/i18n';

const { t } = i18n.global;

export const useAccessLog = defineStore('accessLog', {
  state: () => ({
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
    auditOptions: {
      OPObjectType: [
        {
          name: t('网关'),
          value: 'api',
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
          name: t('版本'),
          value: 'resource_version',
        },
        {
          name: t('发布'),
          value: 'release',
        },
        {
          name: t('策略'),
          value: 'access_strategy',
        },
        {
          name: t('IP分组'),
          value: 'ip_group',
        },
        {
          name: t('标签'),
          value: 'api_label',
        },
        {
          name: t('插件'),
          value: 'plugin',
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
    datepickerShortcuts: state => state.datepickerShortcuts,
    shortcutsInDay: state => state.shortcutsInDay,
    alarmStrategyOptions: state => state.alarmStrategyOptions,
    alarmStatus: state => state.alarmStatus,
    methodList: state => state.methodList,
    SDKLanguageList: state => state.SDKLanguageList,
    auditOptions: state => state.auditOptions,
  },
});
