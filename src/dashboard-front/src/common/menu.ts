
import { IMenu } from '@/types';
import { useUser } from '@/store';
const user = useUser();

export const menuData: IMenu[]  = [
  {
    name: 'apigwStageManage',
    enabled: true,
    title: '环境管理',
    icon: 'components',
    children: [
      {
        name: 'apigwStageOverview',
        enabled: true,
        title: '环境概览',
      },
      {
        name: 'apigwReleaseHistory',
        enabled: true,
        title: '发布记录',
      },
    ],
  },
  {
    name: 'apigwBackendService',
    enabled: true,
    title: '后端服务',
    icon: 'panel-permission',
  },
  {
    name: 'apigwResourceManage',
    enabled: true,
    title: '资源管理',
    icon: 'runtime',
    children: [
      {
        name: 'apigwResource',
        enabled: true,
        title: '资源配置',
      },
      {
        name: 'apigwResourceVersion',
        enabled: true,
        title: '资源版本',
      },
    ],
  },
  {
    name: 'apigwPermissionManage',
    enabled: true,
    title: '权限管理',
    icon: 'permission',
    children: [
      {
        name: 'apigwPermissionApplys',
        enabled: true,
        title: '权限审批',
      },
      {
        name: 'apigwPermissionApps',
        enabled: true,
        title: '应用权限',
      },
      {
        name: 'apigwPermissionRecords',
        enabled: true,
        title: '审批历史',
      },
    ],
  },
  {
    name: 'apigwOperatingData',
    enabled: user.featureFlags?.ENABLE_RUN_DATA,
    title: '运行数据',
    icon: 'bar-chart',
    children: [
      {
        name: 'apigwAccessLog',
        enabled: true,
        title: '流水日志',
      },
      {
        name: 'apigwReport',
        enabled: user.featureFlags?.ENABLE_RUN_DATA_METRICS,
        title: '统计报表',
      },
    ],
  },
  {
    name: 'apigwMonitorAlarm',
    title: '监控告警',
    icon: 'monitor',
    enabled: user.featureFlags?.ENABLE_MONITOR,
    children: [
      {
        name: 'apigwMonitorAlarmStrategy',
        title: '告警策略',
        enabled: true,
      },
      {
        name: 'apigwMonitorAlarmHistory',
        title: '告警历史',
        enabled: true,
      },
    ],
  },
  {
    name: 'apigwOnlineTest',
    enabled: true,
    title: '在线调试',
    icon: 'debug',
  },
  {
    name: 'apigwBasicInfo',
    enabled: true,
    title: '基本信息',
    icon: 'document',
  },
  {
    name: 'apigwOperateRecords',
    enabled: true,
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
