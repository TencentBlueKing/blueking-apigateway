interface IPermission {
  id: number;
  bk_app_code: string;
  resource_id: number;
  resource_name: string;
  resource_path: string;
  resource_method: string;
  expires: string;
  grant_dimension: string;
  grant_type: string;
  renewable: boolean;
  detail?: unknown[];
}

interface IFilterValues {
  id: number | string
  name: string
  values: FilterValue[]
  type?: string
}

type FilterValue = { id: number | string, name: string };

interface IResource {
  id: number;
  method: string;
  name: string;
  path: string;
}

export {
  IPermission,
  IFilterValues,
  FilterValue,
  IResource,
};
