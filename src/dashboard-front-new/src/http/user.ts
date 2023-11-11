import fetch from './fetch';

const { BK_DASHBOARD_URL } = window;

export const getUser = () => fetch.get(`${BK_DASHBOARD_URL}/accounts/userinfo/`);
