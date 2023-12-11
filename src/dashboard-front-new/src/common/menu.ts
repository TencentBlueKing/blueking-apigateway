
import { IMenu } from '@/types';
export const menuData: IMenu[]  = [
  {
    name: 'apigwStageManage',
    title: '环境管理',
    icon: 'components',
    children: [
      {
        name: 'apigwStageOverview',
        title: '环境概览',
      },
      {
        name: 'apigwReleaseHistory',
        title: '发布记录',
      },
    ],
  },
  {
    name: 'apigwResourceManage',
    title: '资源管理',
    icon: 'runtime',
    children: [
      {
        name: 'apigwResource',
        title: '资源配置',
      },
      {
        name: 'apigwResourceVersion',
        title: '资源版本',
      },
    ],
  },
  {
    name: 'apigwBackendService',
    title: '后端服务',
    icon: 'panel-permission',
  },
  {
    name: 'apigwPermissionManage',
    title: '权限管理',
    icon: 'permission',
    children: [
      {
        name: 'apigwPermissionApplys',
        title: '权限审批',
      },
      {
        name: 'apigwPermissionApps',
        title: '应用权限',
      },
      {
        name: 'apigwPermissionRecords',
        title: '审批历史',
      },
    ],
  },
  {
    name: 'apigwOperatingData',
    title: '运行数据',
    icon: 'bar-chart',
    children: [
      {
        name: 'apigwAccessLog',
        title: '流水日志',
      },
      {
        name: 'apigwReport',
        title: '统计报表',
      },
    ],
  },
  {
    name: 'apigwMonitorAlarm',
    title: '监控告警',
    icon: 'monitor',
    children: [
      {
        name: 'apigwMonitorAlarmStrategy',
        title: '告警策略',
      },
      {
        name: 'apigwMonitorAlarmHistory',
        title: '告警历史',
      },
    ],
  },
  {
    name: 'apigwOnlineTest',
    title: '在线调试',
    icon: 'debug',
  },
  {
    name: 'apigwBasicInfo',
    title: '基本信息',
    icon: 'document',
  },
  {
    name: 'apigwOperateRecords',
    title: '操作记录',
    icon: 'audit',
  },
];


export const componentsMenu: IMenu[] = [
  {
    name: 'componentsIntro',
    title: '简介',
    icon: 'component-intro',
  },
  {
    name: 'componentsSystem',
    title: '系统管理',
    icon: 'system-mgr',
  },
  {
    name: 'componentsManage',
    title: '组件管理',
    icon: 'components',
  },
  {
    name: 'componentsCategory',
    title: '文档分类',
    icon: 'document',
  },
  {
    name: 'componentsPermission',
    title: '权限管理',
    icon: 'my-perm',
    children: [
      {
        name: 'permissionApply',
        title: '权限审批',
      },
      {
        name: 'permissionPower',
        title: '应用权限',
      },
      {
        name: 'permissionRecord',
        title: '审批历史',
      },
    ],
  },
  {
    name: 'componentsRuntimeData',
    title: '实时运行数据',
    icon: 'runtime',
  },
];
