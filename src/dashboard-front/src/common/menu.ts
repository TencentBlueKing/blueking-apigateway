import i18n from '@/language/i18n';

import { IMenu } from '@/types';
import { useUser } from '@/store';

const { t } = i18n.global;

export const createMenuData = (): IMenu[] => {
  const user = useUser();
  return [
    // {
    //   name: 'apigwStageManage',
    //   enabled: true,
    //   title: t('环境管理'),
    //   icon: 'resource',
    //   children: [
    //     {
    //       name: 'apigwStageOverview',
    //       enabled: true,
    //       title: t('环境概览'),
    //     },
    //   ],
    // },
    // {
    //   name: 'apigwStageOverview',
    //   enabled: true,
    //   title: t('环境概览'),
    //   icon: 'resource',
    // },
    {
      name: 'apigwStageManage',
      enabled: true,
      title: t('环境管理'),
      icon: 'resource',
      children: [
        {
          name: 'apigwStageOverview',
          enabled: true,
          title: t('环境概览'),
        },
        {
          name: 'apigwReleaseHistory',
          enabled: true,
          title: t('发布记录'),
        },
      ],
    },
    {
      name: 'apigwBackendService',
      enabled: true,
      title: t('后端服务'),
      icon: 'fuwuguanli',
    },
    {
      name: 'apigwResourceManage',
      enabled: true,
      title: t('资源管理'),
      icon: 'ziyuanguanli',
      children: [
        {
          name: 'apigwResource',
          enabled: true,
          title: t('资源配置'),
        },
        {
          name: 'apigwResourceVersion',
          enabled: true,
          title: t('资源版本'),
        },
      ],
    },
    {
      name: 'apigwPermissionManage',
      enabled: true,
      title: t('权限管理'),
      icon: 'quanxianguanli',
      children: [
        {
          name: 'apigwPermissionApplys',
          enabled: true,
          title: t('权限审批'),
        },
        {
          name: 'apigwPermissionApps',
          enabled: true,
          title: t('应用权限'),
        },
        {
          name: 'apigwPermissionRecords',
          enabled: true,
          title: t('审批历史'),
        },
      ],
    },
    {
      name: 'apigwOperatingData',
      enabled: user.featureFlags?.ENABLE_RUN_DATA,
      title: t('运行数据'),
      icon: 'keguancexing',
      children: [
        {
          name: 'apigwAccessLog',
          enabled: true,
          title: t('流水日志'),
        },
        {
          name: 'apigwReport',
          enabled: user.featureFlags?.ENABLE_RUN_DATA_METRICS,
          title: t('统计报表'),
        },
      ],
    },
    {
      name: 'apigwMonitorAlarm',
      title: t('监控告警'),
      // icon: 'monitor',
      icon: 'notification',
      enabled: user.featureFlags?.ENABLE_MONITOR,
      children: [
        {
          name: 'apigwMonitorAlarmStrategy',
          title: t('告警策略'),
          enabled: true,
        },
        {
          name: 'apigwMonitorAlarmHistory',
          title: t('告警记录'),
          enabled: true,
        },
      ],
    },
    {
      name: 'apigwOnlineTest',
      enabled: true,
      title: t('在线调试'),
      icon: 'zaixiandiaoshi',
    },
    {
      name: 'apigwBasicInfo',
      enabled: true,
      title: t('基本信息'),
      icon: 'jibenxinxi',
    },
    {
      name: 'apigwOperateRecords',
      enabled: true,
      title: t('操作记录'),
      icon: 'history',
    },
  ];
};

// export const menuData: IMenu[]  = [
//   {
//     name: 'apigwStageManage',
//     enabled: true,
//     title: '环境管理',
//     icon: 'resource',
//     children: [
//       {
//         name: 'apigwStageOverview',
//         enabled: true,
//         title: '环境概览',
//       },
//     ],
//   },
//   {
//     name: 'apigwBackendService',
//     enabled: true,
//     title: '后端服务',
//     icon: 'fuwuguanli',
//   },
//   {
//     name: 'apigwResourceManage',
//     enabled: true,
//     title: '资源管理',
//     icon: 'ziyuanguanli',
//     children: [
//       {
//         name: 'apigwResource',
//         enabled: true,
//         title: '资源配置',
//       },
//       {
//         name: 'apigwResourceVersion',
//         enabled: true,
//         title: '资源版本',
//       },
//     ],
//   },
//   {
//     name: 'apigwPermissionManage',
//     enabled: true,
//     title: '权限管理',
//     icon: 'quanxianguanli',
//     children: [
//       {
//         name: 'apigwPermissionApplys',
//         enabled: true,
//         title: '权限审批',
//       },
//       {
//         name: 'apigwPermissionApps',
//         enabled: true,
//         title: '应用权限',
//       },
//       {
//         name: 'apigwPermissionRecords',
//         enabled: true,
//         title: '审批历史',
//       },
//     ],
//   },
//   {
//     name: 'apigwOperatingData',
//     enabled: user.featureFlags?.ENABLE_RUN_DATA,
//     title: '运行数据',
//     icon: 'keguancexing',
//     children: [
//       {
//         name: 'apigwAccessLog',
//         enabled: true,
//         title: '流水日志',
//       },
//       {
//         name: 'apigwReport',
//         enabled: user.featureFlags?.ENABLE_RUN_DATA_METRICS,
//         title: '统计报表',
//       },
//     ],
//   },
//   {
//     name: 'apigwMonitorAlarm',
//     title: '监控告警',
//     icon: 'monitor',
//     enabled: user.featureFlags?.ENABLE_MONITOR,
//     children: [
//       {
//         name: 'apigwMonitorAlarmStrategy',
//         title: '告警策略',
//         enabled: true,
//       },
//       {
//         name: 'apigwMonitorAlarmHistory',
//         title: '告警历史',
//         enabled: true,
//       },
//     ],
//   },
//   {
//     name: 'apigwOnlineTest',
//     enabled: true,
//     title: '在线调试',
//     icon: 'zaixiandiaoshi',
//   },
//   {
//     name: 'apigwBasicInfo',
//     enabled: true,
//     title: '基本信息',
//     icon: 'jibenxinxi',
//   },
//   {
//     name: 'apigwOperateRecords',
//     enabled: true,
//     title: '操作记录',
//     icon: 'history',
//   },
// ];

export const componentsMenu: IMenu[] = [
  {
    name: 'componentsIntro',
    title: t('简介'),
    icon: 'component-intro',
  },
  {
    name: 'componentsSystem',
    title: t('系统管理'),
    icon: 'system-mgr',
  },
  {
    name: 'componentsManage',
    title: t('组件管理'),
    icon: 'components',
  },
  {
    name: 'componentsCategory',
    title: t('文档分类'),
    icon: 'document',
  },
  // {
  //   name: 'componentsPermission',
  //   title: t('权限管理'),
  //   icon: 'my-perm',
  //   children: [
  //     {
  //       name: 'permissionApply',
  //       title: t('权限审批'),
  //     },
  //     {
  //       name: 'permissionPower',
  //       title: t('应用权限'),
  //     },
  //     {
  //       name: 'permissionRecord',
  //       title: t('审批历史'),
  //     },
  //   ],
  // },
  {
    name: 'componentsRuntimeData',
    title: t('实时运行数据'),
    icon: 'runtime',
  },
];

export const platformToolsMenu: IMenu[] = [
  {
    name: 'platformToolsToolbox',
    title: t('工具箱'),
    icon: 'gongjuxiang',
  },
  {
    name: 'platformToolsAutomatedGateway',
    title: t('自动化接入网关'),
    icon: 'zidongjieru',
  },
];
