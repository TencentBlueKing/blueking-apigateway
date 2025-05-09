/**
 * IPermission 接口定义了权限对象的结构
 */
interface IPermission {
  id: number; // 权限ID
  bk_app_code: string; // 蓝鲸应用编码
  resource_id: number; // 资源ID
  resource_name: string; // 资源名称
  resource_path: string; // 资源路径
  resource_method: string; // 资源方法
  expires: string; // 过期时间
  grant_dimension: string; // 授权维度
  grant_type: string; // 授权类型
  renewable: boolean; // 是否可续期
  detail?: unknown[]; // 详细信息（可选）
}

/**
 * IFilterValues 接口定义了过滤器值对象的结构
 */
interface IFilterValues {
  id: number | string; // 过滤器ID
  name: string; // 过滤器名称
  values: FilterValue[]; // 过滤器值数组
  type?: string; // 过滤器类型（可选）
}

/**
 * FilterValue 类型定义了过滤器值的结构
 */
type FilterValue = {
  id: number | string; // 过滤器值ID
  name: string; // 过滤器值名称
};

/**
 * IResource 接口定义了资源对象的结构
 */
interface IResource {
  id: number; // 资源ID
  method: string; // 资源方法
  name: string; // 资源名称
  path: string; // 资源路径
}

export {
  IPermission,
  IFilterValues,
  FilterValue,
  IResource,
};
