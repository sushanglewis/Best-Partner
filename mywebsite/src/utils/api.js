import axios from "axios";

const api = axios.create({
  baseURL: "/api", // 可根据后端实际地址调整
  timeout: 10000,
});

export const get = (url, params) => api.get(url, { params });
export const post = (url, data) => api.post(url, data);
export const put = (url, data) => api.put(url, data);
export const del = (url, params) => api.delete(url, { params });

export default api;
