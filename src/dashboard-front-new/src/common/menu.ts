
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
    icon: 'components',
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
    name: 'apigwOnlineTest',
    title: '在线调试',
    icon: 'debug',
  },
  {
    name: 'apigwBasicInfo',
    title: '基本信息',
    icon: 'document',
  },
];
