import fetch from './fetch';
import { json2Query } from '@/common/util';
const { BK_DASHBOARD_URL } = window;


/**
 *  获取组件系统列表
 * @param board
 * @param data 查询参数
 */
export const getComponentSystemList = (board: string, data: any = {}) => fetch.get(`${BK_DASHBOARD_URL}/docs/esb/boards/${board}/systems/?${json2Query(data)}`);

/**
 *  获取组件系统信息
 * @param board
 * @param system_name  系统名称
 */
export const getComponenSystemDetail = (board: string, system_name: string) => fetch.get(`${BK_DASHBOARD_URL}/docs/esb/boards/${board}/systems/${system_name}/`);

/**
 *  查询指定组件系统下的组件 API 列表，仅返回公开的组件
 * @param board
 * @param data 查询参数
 * @param system_name  系统名称
 */
export const getSystemAPIList = (board: string, system_name: string, data: any) => fetch.get(`${BK_DASHBOARD_URL}/docs/esb/boards/${board}/systems/${system_name}/components/?${json2Query(data)}`);

/**
 *  查询组件 API，根据筛选条件模糊搜索，仅返回前 30 条记录
 * @param board
 * @param data 查询参数
 * @param system_name  系统名称
 */
export const searchAPI = (board: string, system_name: string, data: any) => fetch.get(`${BK_DASHBOARD_URL}/docs/esb/boards/${board}/systems/${system_name}/components/search/?${json2Query(data)}`);

/**
 *  获取组件 API 文档，仅获取当前语言（中文/英文）的文档
 * @param board
 * @param system_name  系统名称
 * @param component_name   组件名称
 */
export const getAPIDoc = (board: string, system_name: string, component_name: string) => fetch.get(`${BK_DASHBOARD_URL}/docs/esb/boards/${board}/systems/${system_name}/components/${component_name}/doc/`);
