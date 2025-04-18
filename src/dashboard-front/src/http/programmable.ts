/*
* 可编程网关相关 API
*  */

import fetch from './fetch';
import { json2Query } from '@/common/util';

interface IFrameworkStep {
  name: string;
  display_name: string;
  skipped: boolean;
}

interface IInstanceStep {
  name: string;
  display_name: string;
  skipped: boolean;
  uuid: string;
  status: null | string;
  start_time: null | string;
  complete_time: null | string;
}

interface SourceInfo {
  source_type: string;
  type: string;
  trunk_url: string;
  repo_url: string;
  source_dir: string;
  repo_fullname: string;
  diff_feature: {
    method: null | string;
    enabled: boolean;
  };
  linked_to_internal_svn: boolean;
  display_name: string;
}

interface ServiceInfo {
  name: string;
  display_name: string;
  is_provisioned: boolean;
  service_id: string;
  category_id: number;
}

interface HelpDoc {
  title: string;
  location: string;
  short_description: string;
  link: string;
  name: string;
  text: string;
  description: string;
}

interface DisplayBlocksPreparation {
  source_info: SourceInfo;
  services_info: ServiceInfo[];
  prepare_help_docs: HelpDoc[];
}

interface RuntimeInfo {
  image: string;
  slugbuilder: null | string;
  slugrunner: null | string;
  buildpacks: {
    id: number;
    language: string;
    name: string;
    display_name: string;
    description: string;
  }[];
}

interface DisplayBlocksBuild {
  runtime_info: RuntimeInfo;
  build_help_docs: HelpDoc[];
}

interface AccessInfo {
  address: string;
  type: string;
}

interface DisplayBlocksRelease {
  access_info: AccessInfo;
  release_help_docs: HelpDoc[];
}

export interface IEvent {
  id: number;
  event: string;
  data: string;
}

export interface IEventsFramework {
  display_name: string;
  type: string;
  steps: IFrameworkStep[];
  display_blocks: DisplayBlocksPreparation | DisplayBlocksBuild | DisplayBlocksRelease;
}

export interface IEventsInstance {
  display_name: string;
  type: string;
  steps: IInstanceStep[];
  display_blocks: DisplayBlocksPreparation | DisplayBlocksBuild | DisplayBlocksRelease;
  uuid: string;
  status: null | string;
  start_time: null | string;
  complete_time: null | string;
}

interface IPaasDeployInfo {
  events: IEvent[];
  events_framework: IEventsFramework[];
  events_instance: IEventsInstance[];
}

interface IEventResponse {
  created_by: string;
  created_time: string;
  duration: number;
  events: unknown[];
  events_template: unknown[];
  id: number;
  paas_deploy_info: IPaasDeployInfo;
  resource_version_display: string;
  source: string;
  stage: {
    id: number;
    name: string;
  };
  status: string;
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
  branch: string;
  commit_id: string;
  created_by: string | null;
  created_time: string;
  deploy_id: string;
  latest_deployment: {
    branch: string;
    commit_id: string;
    deploy_id: string;
    history_id: number;
    version: string;
  };
  repo_info: {
    branch_commit_info: Record<string, string>;
    branch_list: string[];
    repo_url: string;
  };
  version: string;
}> => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/stages/${stageId}/programmable/`);

// 获取下一个发布版本号
export const getProgrammableStageNextVersion = (apigwId: number, data: {
  stage_name: string,
  version_type: string
}) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resource-versions/programmable/next-deploy-version/?${json2Query(data)}`);

// 查询发布事件
export const getProgrammableDeployEvents = (apigwId: number, deploy_id: number): Promise<IEventResponse> => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/releases/programmable/deploy/${deploy_id}/histories/events/`);
