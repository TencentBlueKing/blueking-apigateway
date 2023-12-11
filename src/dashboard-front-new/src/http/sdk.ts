import fetch from './fetch';
import { json2Query } from '@/common/util';

const { BK_DASHBOARD_URL } = window;

/**
 *  获取所有网关 SDK，单个 SDK 仅返回最新版本 SDK 信息
 * @param data 查询参数
 */
export const getGatewaySDKlist = (data: any) => fetch.get(`${BK_DASHBOARD_URL}/docs/sdks/?${json2Query(data)}`);

/**
 *  获取指定语言（python）的网关 SDK 说明文档
 * @param data 查询参数
 */
export const getGatewaySDKDoc = (data: any) => fetch.get(`${BK_DASHBOARD_URL}/docs/sdks/doc/?${json2Query(data)}`);

/**
 *  获取所有的组件 SDK 列表，单个 SDK 仅返回最新版本 SDK 信息
 * @param board
 * @param data 查询参数
 */
export const getESBSDKlist = (board: string, data: any) => fetch.get(`${BK_DASHBOARD_URL}/docs/esb/boards/${board}/sdks/?${json2Query(data)}`);

/**
 *  获取指定语言（python）组件 SDK 的调用样例
 * @param board
 * @param data 查询参数
 */
export const getESBSDKDoc = (board: string, data: any) => fetch.get(`${BK_DASHBOARD_URL}/docs/esb/boards/${board}/sdks/doc/?${json2Query(data)}`);

/**
 *  获取指定语言（python） 组件 SDK 的信息
 * @param board
 * @param data 查询参数
 */
export const getESBSDKDetail = (board: string, data: any) => fetch.get(`${BK_DASHBOARD_URL}/docs/esb/boards/${board}/sdks/latest/?${json2Query(data)}`);
