import { personalInfo, summaryCards, experiences, projects } from "./config";

// 模拟异步获取内容
export const fetchPersonalInfo = async () => Promise.resolve(personalInfo);
export const fetchSummaryCards = async () => Promise.resolve(summaryCards);
export const fetchExperiences = async () => Promise.resolve(experiences);
export const fetchProjects = async () => Promise.resolve(projects);

// 模拟内容更新（实际可对接后端）
export const updatePersonalInfo = async (data) =>
  Promise.resolve({ ...personalInfo, ...data });
export const updateSummaryCards = async (cards) => Promise.resolve(cards);
export const updateExperiences = async (list) => Promise.resolve(list);
export const updateProjects = async (list) => Promise.resolve(list);
