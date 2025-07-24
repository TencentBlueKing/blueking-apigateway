/*
* 可编程网关相关 API
*  */

import http from '../http';

const path = '/gateways';

/**
 * 新增标签
 * @param apigwId 网关id
 * @param data 标签名称
 */
export const createLabels = (apigwId: number, data: { name: string }) => http.post(`${path}/${apigwId}/labels/`, data);

/**
 * 删除标签
 * @param apigwId 网关id
 * @param labelsId 标签id
 */
export const deleteLabels = (apigwId: number, labelsId: number) => http.delete(`${path}/${apigwId}/labels/${labelsId}/`);

/**
 * 更新标签
 * @param apigwId 网关id
 * @param labelsId 标签id
 * @param data 标签数据
 */
export const updateLabel = (apigwId: number, labelsId: number, data: { name: string }) =>
  http.put(`${path}/${apigwId}/labels/${labelsId}/`, data);
