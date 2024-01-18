import { getCurrentInstance } from 'vue';

export const useGetGlobalProperties = () => {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { emit, appContext: { app: { config: { globalProperties } } } } = getCurrentInstance();

  return { ...globalProperties };
};
