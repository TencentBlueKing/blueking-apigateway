import http from '../http';

const path = '/gateways';

export interface IStageListItem {
  id: number
  name: string
  description: string
  description_en: string
  status: number
  created_time: string
  release: {
    status: string
    created_time: string
    created_by: string
  }
  resource_version: {
    version: string
    id: number
    schema_version: string
  }
  publish_id: number
  publish_version: string
  publish_validate_msg: string
  new_resource_version: string
}

export const getStageList = (apigwId: number) => http.get<IStageListItem[]>(`${path}/${apigwId}/stages/`);

export const getStageDetail = (apigwId: number, stageId: number) =>
  http.get<IStageListItem>(`${path}/${apigwId}/stages/${stageId}`);

export const createStage = (apigwId: number, data: any) => http.post(`${path}/${apigwId}/stages/`, data);

export const deleteStage = (apigwId: number, stageId: number) =>
  http.delete(`${path}/${apigwId}/stages/${stageId}/`);

export const putStage = (apigwId: number, stageId: number, data: any) =>
  http.put(`${http}/${apigwId}/stages/${stageId}/`, data);

export const toggleStatus = (apigwId: number, stageId: number, param: { status: number }) =>
  http.put(`${path}/${apigwId}/stages/${stageId}status/`, param);

export const getStageBackends = (apigwId: number, stageId: number) =>
  http.get(`${path}/${apigwId}/stages/${stageId}/backends/`);

export const getStageVars = (apigwId: number, stageId: number) => http.get(`${path}/${apigwId}/stages/${stageId}/vars/`);

export const putStageVars = (apigwId: number, stageId: number, data: any) => http.put(`${path}/${apigwId}/stages/${stageId}/vars/`, data);
