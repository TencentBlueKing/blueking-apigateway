/** /gateways/{gateway_id}/plugins/ [GET] */
export interface IGatewaysPluginsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 名称关键字 */
  keyword?: string
  /** 范围类型：stage or resource */
  scope_type: 'stage' | 'resource'
  /** 范围 id: stage_id or resource_id */
  scope_id: number
  /** 标签 */
  tag?: string
}

/** /gateways/{gateway_id}/plugins/-/tags/ [GET] */
export interface IGatewaysPluginsTagsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

/** /gateways/{gateway_id}/plugins/{code}/bindings/ [GET] */
export interface IGatewaysPluginsBindingsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

/** /gateways/{gateway_id}/plugins/{scope_type}/{scope_id}/ [GET] */
export interface IGatewaysPluginsReadQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

// POST /gateways/{gateway_id}/plugins/{scope_type}/{scope_id}/{code}/configs/ - 创建一个插件，并且绑定到对应的 scope_type + scope_id
export interface IPluginConfigBaseSLZ {
  id?: number
  name?: string
  yaml?: string
  type_id: number
}

/**
 * GET /gateways/{gateway_id}/plugins/
 */
export interface IPluginTypeListOutput {
  id: number
  name: string
  code: string
  is_public: boolean
  description: string
  notes: string
  related_scope_count: Record<'stage' | 'resource', number>
  is_bound: boolean
  tags: string[]
}

/**
 * GET /gateways/{gateway_id}/plugins/-/tags/
 */
export interface IPluginTypeTagsOutput {
  tags: string[]
}

/**
 * GET /gateways/{gateway_id}/plugins/{code}/bindings/
 */
export interface IPluginBindingListOutput {
  stages: {
    id: number
    name: string
  }[]
  resources: {
    id: number
    name: string
  }[]
}

/**
 * GET /gateways/{gateway_id}/plugins/{scope_type}/{scope_id}/
 */
export interface IScopePluginConfigListOutput {
  code: string
  name: string
  config: {
    [key: string]: string | null
  }
  config_id: number
  related_scope_count: IPluginTypeListOutput['related_scope_count']
}

/**
 * GET /gateways/{gateway_id}/plugins/{scope_type}/{scope_id}/{code}/configs/{id}/
 */
export interface IPluginConfigRetrieveOutput {
  id: number
  name: string | null
  yaml: string | null
  type_id: number
}
