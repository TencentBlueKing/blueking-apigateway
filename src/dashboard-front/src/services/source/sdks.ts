import http from '../http';

const path = '/gateways';

export const getSDKList = (apigwId: number, data: any) => http.get(`${path}/${apigwId}/sdks/`, data);

export const createSDK = (apigwId: number, data: any) => http.post(`${path}/${apigwId}/sdks/`, data);
