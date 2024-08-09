import fetch from './fetch';
import { json2Query, blobDownLoad } from '@/common/util';

const { BK_DASHBOARD_URL } = window;

/**
 *  资源列表数据
 * @param apigwId 网关id
 * @returns
 */
export const getResourceListData = (apigwId: number, data: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resources/?${json2Query(data)}`);

/**
 *  创建资源
 * @param apigwId 网关id
 * @param data 网关资源数据
 * @returns
 */
export const createResources = (apigwId: number, data: any) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resources/`, data);

/**
 *  更新资源
 * @param apigwId 网关id
 * @param resourceId 网关资源id
 * @param data 网关资源数据
 * @returns
 */
export const updateResources = (apigwId: number, resourceId: number, data: any) => fetch.put(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resources/${resourceId}/`, data);

/**
 *  获取资源详情
 * @param apigwId 网关id
 * @param resourceId 网关资源id
 * @returns
 */
export const getResourceDetailData = (apigwId: number, resourceId: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resources/${resourceId}/`);


/**
 *  删除资源
 * @param apigwId 网关id
 * @param resourceId 网关资源id
 * @returns
 */
export const deleteResources = (apigwId: number, resourceId: number) => fetch.delete(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resources/${resourceId}/`);

/**
 *  批量删除资源
 * @param apigwId 网关id
 * @param resourceIds 网关资源id组
 * @returns
 */
export const batchDeleteResources = (apigwId: number, data: {ids: number[]}) => fetch.delete(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resources/batch/`, data);

/**
 *  批量编辑资源
 * @param apigwId 网关id
 * @param resourceIds 网关资源id组
 * @returns
 */
export const batchEditResources = (apigwId: number, data: {ids: number[], is_public: boolean, allow_apply_permission: boolean}) => fetch.put(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resources/batch/`, data);

// 校验资源后端地址
export const backendsPathCheck = (apigwId: number, data: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resources/backend-path/check/?${json2Query(data)}`);

/**
 *  资源版本详情
 * @param apigwId 网关id
 * @param versionId 版本id
 * @returns
 */
export const getResourceVersionsInfo = (apigwId: number, id: number, data?: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resource-versions/${id}/?${json2Query(data)}`);

/**
 *  资源版本列表
 * @param apigwId 网关id
 * @returns
 */
export const getResourceVersionsList = (apigwId: number, data: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resource-versions/?${json2Query(data)}`);

/**
 *  sdk列表查询接口
 * @param apigwId 网关id
 * @returns
 */
export const getSdksList = (apigwId: number, data: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/sdks/?${json2Query(data)}`);

/**
 *  资源版本对比接口
 * @param apigwId 网关id
 * @returns
 */
export const resourceVersionsDiff = (apigwId: number, data: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resource-versions/diff/?${json2Query(data)}`);

/**
 *  sdk创建接口
 * @param apigwId 网关id
 * @param data 数据
 * @returns
 */
export const createSdks = (apigwId: number, data: any) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/sdks/`, data);

/**
 * 导出资源
 * @param apigwId 网关id
 * @param data 导出参数
 */

export const exportResources = async (apigwId: number, data: any) => {
  const res = await fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resources/export/`, data, { responseType: 'blob' });
  return blobDownLoad(res);
};

/**
 * 导出文档
 * @param apigwId 网关id
 * @param data 导出参数
 */
export const exportDocs = async (apigwId: number, data: any) => {
  const res = await fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/docs/export/`, data, { responseType: 'blob' });
  return blobDownLoad(res);
};

/**
 * 导入前检查
 * @param apigwId 网关id
 * @param data 检查参数
 * @param config 拦截器选项
 */
export const checkResourceImport = (apigwId: number, data: any, config: any = {}) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resources/import/check/`, data, config);

/**
 * 导入资源
 * @param apigwId 网关id
 * @param data 导入参数
 */
export const importResource = (apigwId: number, data: any) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resources/import/`, data);

/**
 * 导入资源文档
 * @param apigwId 网关id
 * @param data 导入参数
 */
export const importResourceDoc = (apigwId: number, data: any) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/docs/import/by-archive/`, data, { responseType: 'formData' });

/**
 * 导入资源文档by swagger
 * @param apigwId 网关id
 * @param data 导入参数
 */
export const importResourceDocSwagger = (apigwId: number, data: any) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/docs/import/by-swagger/`, data);

/**
 * 获取资源文档数据
 * @param apigwId 网关id
 * @param resourceId 资源id
 */
export const getResourceDocs = (apigwId: number, resourceId: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resources/${resourceId}/docs/`);

/**
 * 获取资源文档预览数据
 * @param apigwId 网关id
 * @param data 资源参数
 */
export const getResourceDocPreview = (apigwId: number, data: any) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resources/import/doc/preview/`, data);

/**
 * 保存资源文档数据
 * @param apigwId 网关id
 * @param resourceId 资源id
 * @param data 文档内容
 */
export const saveResourceDocs = (apigwId: number, resourceId: number, data: any) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resources/${resourceId}/docs/`, data);

/**
 * 更新资源文档数据
 * @param apigwId 网关id
 * @param resourceId 资源id
 * @param data 文档内容
 * @param docId 文档id
 */
export const updateResourceDocs = (apigwId: number, resourceId: number, data: any, docId: number) => fetch.put(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resources/${resourceId}/docs/${docId}/`, data);

/**
 * 删除资源文档数据
 * @param apigwId 网关id
 * @param resourceId 资源id
 * @param docId 文档id
 */
export const deleteResourceDocs = (apigwId: number, resourceId: number, docId: number) => fetch.delete(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resources/${resourceId}/docs/${docId}/`);

/**
 * 是否需要创建新资源版本
 * @param apigwId 网关id
 */
export const checkNeedNewVersion = (apigwId: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resource-versions/need-new-version/`, { globalError: false });

/**
 * 获取建议的版本
 * @param apigwId 网关id
 */
export const getNextVersion = (apigwId: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resource-versions/next-version/`);

/**
 * 设置标签
 * @param apigwId 网关id
 * @param resourceId 资源id
 * @param data 标签数据
 */
export const updateResourcesLabels = (apigwId: number, resourceId: number, data: any) => fetch.put(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resources/${resourceId}/labels/`, data);

/**
 * 新增标签
 * @param apigwId 网关id
 * @param data 标签名称
 */
export const createResourcesLabels = (apigwId: number, data: {name: string}) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/labels/`, data);

/**
 * 删除标签
 * @param apigwId 网关id
 * @param labelsId 标签id
 */
export const deleteResourcesLabels = (apigwId: number, labelsId: number) => fetch.delete(`${BK_DASHBOARD_URL}/gateways/${apigwId}/labels/${labelsId}/`);

/**
 * 更新标签
 * @param apigwId 网关id
 * @param labelsId 标签id
 * @param data 标签数据
 */
export const updateResourcesLabelItem = (apigwId: number, labelsId: number, data: {name: string}) => fetch.put(`${BK_DASHBOARD_URL}/gateways/${apigwId}/labels/${labelsId}/`, data);
