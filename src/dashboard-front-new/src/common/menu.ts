
import { IMenu } from '@/types';
export const menuData: IMenu[]  = [
  {
    name: 'apigwStageManage',
    title: '环境管理',
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
];
