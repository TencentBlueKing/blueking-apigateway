/*
* 可编程网关相关 API
*  */

import fetch from './fetch';
import { json2Query } from '@/common/util';

// 框架步骤接口
interface IFrameworkStep {
  name: string; // 步骤名称
  display_name: string; // 显示名称
  skipped: boolean; // 是否跳过
}

// 实例步骤接口
interface IInstanceStep {
  name: string; // 步骤名称
  display_name: string; // 显示名称
  skipped: boolean; // 是否跳过
  uuid: string; // 唯一标识符
  status: null | string; // 状态
  start_time: null | string; // 开始时间
  complete_time: null | string; // 完成时间
}

// 源信息接口
interface SourceInfo {
  source_type: string; // 源类型
  type: string; // 类型
  trunk_url: string; // 主干URL
  repo_url: string; // 仓库URL
  source_dir: string; // 源目录
  repo_fullname: string; // 仓库全名
  diff_feature: {
    method: null | string; // 差异方法
    enabled: boolean; // 是否启用
  };
  linked_to_internal_svn: boolean; // 是否链接到内部SVN
  display_name: string; // 显示名称
}

// 服务信息接口
interface ServiceInfo {
  name: string; // 服务名称
  display_name: string; // 显示名称
  is_provisioned: boolean; // 是否已配置
  service_id: string; // 服务ID
  category_id: number; // 类别ID
}

// 帮助文档接口
interface HelpDoc {
  title: string; // 标题
  location: string; // 位置
  short_description: string; // 简短描述
  link: string; // 链接
  name: string; // 名称
  text: string; // 文本
  description: string; // 描述
}

// 准备阶段显示块接口
interface DisplayBlocksPreparation {
  source_info: SourceInfo; // 源信息
  services_info: ServiceInfo[]; // 服务信息数组
  prepare_help_docs: HelpDoc[]; // 准备帮助文档数组
}

// 运行时信息接口
interface RuntimeInfo {
  image: string; // 镜像
  slugbuilder: null | string; // 构建器
  slugrunner: null | string; // 运行器
  buildpacks: {
    id: number; // 构建包ID
    language: string; // 语言
    name: string; // 名称
    display_name: string; // 显示名称
    description: string; // 描述
  }[];
}

// 构建阶段显示块接口
interface DisplayBlocksBuild {
  runtime_info: RuntimeInfo; // 运行时信息
  build_help_docs: HelpDoc[]; // 构建帮助文档数组
}

// 访问信息接口
interface AccessInfo {
  address: string; // 地址
  type: string; // 类型
}

// 发布阶段显示块接口
interface DisplayBlocksRelease {
  access_info: AccessInfo; // 访问信息
  release_help_docs: HelpDoc[]; // 发布帮助文档数组
}

// 事件接口
export interface IEvent {
  id: number; // 事件ID
  event: string; // 事件名称
  data: string; // 事件数据
}

// 事件框架接口
export interface IEventsFramework {
  display_name: string; // 显示名称
  type: string; // 类型
  steps: IFrameworkStep[]; // 步骤数组
  display_blocks: DisplayBlocksPreparation | DisplayBlocksBuild | DisplayBlocksRelease; // 显示块
}

// PaaS事件实例接口
export interface IPaasEventInstance {
  display_name: string; // 显示名称
  type: string; // 类型
  steps: IInstanceStep[]; // 步骤数组
  display_blocks: DisplayBlocksPreparation | DisplayBlocksBuild | DisplayBlocksRelease; // 显示块
  uuid: string; // 唯一标识符
  status: null | string; // 状态
  start_time: null | string; // 开始时间
  complete_time: null | string; // 完成时间
}

// PaaS部署信息接口
interface IPaasDeployInfo {
  deploy_result: {
    logs?: string;
  };
  events: IEvent[]; // 事件数组
  events_framework: IEventsFramework[]; // 事件框架数组
  events_instance: IPaasEventInstance[]; // 事件实例数组
}

// 网关事件接口
export interface IGatewayEvent {
  'id': number; // 事件ID
  'release_history_id': number; // 发布历史ID
  'name': string; // 事件名称
  'step': number; // 步骤
  'status': string; // 状态
  'created_time': string; // 创建时间
  'detail': any; // 详情
}

// 网关事件模板接口
export interface IGatewayEventTemplate {
  'name': string; // 模板名称
  'description': string; // 描述
  'step': number; // 步骤
}

// 事件响应接口
interface IEventResponse {
  created_by: string; // 创建者
  created_time: string; // 创建时间
  duration: number; // 持续时间
  events: IGatewayEvent[]; // 网关事件数组
  events_template: IGatewayEventTemplate[]; // 网关事件模板数组
  id: number; // 响应ID
  paas_deploy_info: IPaasDeployInfo; // PaaS部署信息
  resource_version_display: string; // 资源版本显示
  source: string; // 来源
  stage: {
    id: number; // 阶段ID
    name: string; // 阶段名称
  };
  status: string; // 状态
}

const { BK_DASHBOARD_URL } = window;

// 发布
export const deployReleases = (apigwId: number, data: {
  stage_id: number,
  branch: string,
  commit_id: string,
  version: string,
  comment: string,
}) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/releases/programmable/deploy/`, data, { globalError: false });

// 获取环境详情
export const getProgrammableStageDetail = (apigwId: number, stageId: number): Promise<{
  branch: string; // 分支
  commit_id: string; // 提交ID
  created_by: string | null; // 创建者
  created_time: string; // 创建时间
  deploy_id: string; // 部署ID
  latest_deployment: {
    branch: string; // 分支
    commit_id: string; // 提交ID
    deploy_id: string; // 部署ID
    history_id: number; // 历史ID
    status: string; // 状态
    version: string; // 版本
  };
  repo_info: {
    branch_commit_info: {
      [branch: string]: {
        commit_id: string; // 提交ID
        extra: object; // 额外信息
        last_update: string; // 最后更新
        message: string; // 信息
        type: string; // 类型
      }
    };
    branch_list: string[]; // 分支列表
    repo_url: string; // 仓库URL
  };
  status: string; // 状态
  version: string; // 版本
}> => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/stages/${stageId}/programmable/`);

// 获取下一个发布版本号
export const getStageNextVersion = (apigwId: number, data: {
  stage_name: string, // 阶段名称
  version_type: string // 版本类型
}) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resource-versions/programmable/next-deploy-version/?${json2Query(data)}`);

// 查询部署中的发布事件
export const getDeployEvents = (apigwId: number, deploy_id: string): Promise<IEventResponse> => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/releases/programmable/deploy/${deploy_id}/histories/events/`);

// 查询已完成部署后的发布事件
export const getFinishedDeployEvents = (apigwId: number, history_id: number): Promise<IEventResponse> => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/releases/programmable/deploy/histories/${history_id}/events/`);

// 查询部署历史
export const getDeployHistories = (apigwId: number, data: Record<string, any>): Promise<IEventResponse> => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/releases/programmable/deploy/histories/?${json2Query(data)}`);
