/*
* 使用 lang="tsx" 的组件直接 import 'vue-router' 引入的路由无法使用
* 需要在组件外封装一次，此 hook 即为实现此目的创建
* 现在在 TSX 组件中引入本 hook 就可正常使用 vue-router
*
* 引入：
* import useTsxRouter from './hooks/useTsxRouter';
*
* 使用：
* const { useRouter, onBeforeRouteLeave } = useTsxRouter();
* const router = useRouter();
*
*  */
import { useRouter, onBeforeRouteLeave } from 'vue-router';

export default function useTsxRouter() {
  return {
    useRouter,
    onBeforeRouteLeave,
  };
};
