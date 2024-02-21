import fetch from './fetch';

const { BK_DASHBOARD_URL } = window;
/**
 *  获取文档列表
 */
export const getDocCategorys = () => fetch.get(`${BK_DASHBOARD_URL}/esb/doc-categories/`);

/**
 *  获取某个文档详情
 * @param id 文档id
 */
export const getDocCategoryDetail = (id: number) => fetch.get(`${BK_DASHBOARD_URL}/esb/doc-categories/${id}/`);

/**
 *  新建文档
 * @param data 新建数据
 */
export const addDocCategory = (data: any) => fetch.post(`${BK_DASHBOARD_URL}/esb/doc-categories/`, data);

/**
 *  更新文档
 * @param id 文档id
 * @param data 更新数据
 */
export const updateDocCategory = (id: number, data: any) => fetch.put(`${BK_DASHBOARD_URL}/esb/doc-categories/${id}/`, data);

/**
 *  删除文档
 * @param id 文档id
 */
export const deleteDocCategory = (id: number, data: any) => fetch.delete(`${BK_DASHBOARD_URL}/esb/doc-categories/${id}/`, data);
