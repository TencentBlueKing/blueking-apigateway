import i18n from '@/locales';
import type { IHeaderNav, IMenu } from '@/types/common';

const { t } = i18n.global;

// 我的网关左侧菜单
export function getMyGateWayMenu(): IHeaderNav[] {
  return [
    {
      name: t('我的网关'),
      id: 1,
      url: 'Home',
      enabled: true,
      link: '',
    },
    {
      name: t('组件管理'),
      id: 2,
      url: 'ComponentsMain',
      enabled: true,
      link: '',
    },
    {
      name: t('API 文档'),
      id: 3,
      url: 'ApiDocs',
      enabled: true,
      link: '',
    },
    {
      name: t('平台工具'),
      id: 4,
      url: 'PlatformTools',
      enabled: true,
      link: '',
    },
    {
      name: t('MCP 市场'),
      id: 5,
      url: 'mcpMarket',
      enabled: true,
      link: '',
    },
  ];
}

// 组件管理左侧菜单
export function getComponentsMenu(): IMenu[] {
  return [
    {
      name: 'ComponentsIntro',
      title: t('简介'),
      icon: 'component-intro',
    },
    {
      name: 'ComponentsSystem',
      title: t('系统管理'),
      icon: 'system-mgr',
    },
    {
      name: 'ComponentsManage',
      title: t('组件管理'),
      icon: 'components',
    },
    {
      name: 'ComponentsCategory',
      title: t('文档分类'),
      icon: 'document',
    },
    {
      name: 'ComponentsRuntimeData',
      title: t('实时运行数据'),
      icon: 'runtime',
    },
  ];
}

// 方法名称
export const METHODS_CONSTANTS: {
  id: string
  name: string
}[] = [
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
];
