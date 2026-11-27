/** /gateways/{gateway_id}/releases/programmable/deploy/histories/ [GET] */
export interface IGatewaysReleasesProgrammableDeployHistoriesListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 查询参数关键字 */
  keyword?: string
  /** 环境 id */
  stage_id?: number | null
  /** 创建者 */
  created_by?: string
  /** 开始时间（Unix 秒）；只有起止都传才过滤，闭区间 created_time ∈ [time_start, time_end] */
  time_start?: number | null
  /** 结束时间（Unix 秒） */
  time_end?: number | null
}

/** /gateways/{gateway_id}/resource-versions/programmable/next-deploy-version/ [GET] */
export interface IGatewaysResourceVersionsProgrammableNextDeployVersionReadQuery {
  /** 环境name */
  stage_name: string
  /** 版本类型：major/minor/patch */
  version_type: 'major' | 'minor' | 'patch'
}

// POST /gateways/{gateway_id}/releases/programmable/deploy/ - 编程网关部署接口
export interface IProgrammableDeployCreateInputSLZ {
  stage_id: number
  branch: string
  version_type: string
  commit_id: string
  version: string
  comment: string
}

/**
 * GET /gateways/{gateway_id}/releases/programmable/deploy/histories/
 */
export interface IDeployHistoryListOutput {
  deploy_id: string
  history_id: number
  commit_id: string
  branch: string
  source: string
  stage: {
    id: number
    name: string
  }
  status: string
  created_time: string
  version: string
  created_by: string
}

/**
 * GET /gateways/{gateway_id}/releases/programmable/deploy/histories/{history_id}/events/
 */
export interface IGetDeployEventsByHistoryIdOutput {
  id: number
  stage: {
    id: number
    name: string
  }
  resource_version_display: string
  created_time: string
  created_by: string
  source: string
  duration: number
  status: string
  events: {
    id: number
    release_history_id: number
    name: string
    step: number
    status: string
    created_time: string
    detail: {
      [key: string]: string | null
    }
  }[]
  events_template: any
  paas_deploy_info: any
  data_plane: {
    description: string
    id: number
    name: string
  } | null
}

/**
 * GET /gateways/{gateway_id}/releases/programmable/deploy/{deploy_id}/histories/events/
 */
export interface IGetDeployEventsByDeployIdOutput {
  id: number
  stage: {
    id: number
    name: string
  }
  resource_version_display: string
  created_time: string
  created_by: string
  source: string
  duration: number
  status: string
  events: {
    id: number
    release_history_id: number
    name: string
    step: number
    status: string
    created_time: string
    detail: {
      [key: string]: string | null
    }
  }[]
  events_template: string
  paas_deploy_info: string
  data_plane: {
    description: string
    id: number
    name: string
  } | null
}

/**
 * GET /gateways/{gateway_id}/stages/{id}/programmable/
 */
export interface IProgrammableStageDeployOutput {
  branch: string
  commit_id: string
  created_by: string | null
  created_time: string
  deploy_id: string
  latest_deployment: {
    branch: string
    commit_id: string
    deploy_id: string
    history_id: number
    status: string
    version: string
  }
  repo_info: {
    branch_commit_info: {
      [branch: string]: {
        commit_id: string
        extra: object
        last_update: string
        message: string
        type: string
      }
    }
    branch_list: string[]
    repo_url: string
  }
  status: string
  version: string
}

/** POST /gateways/{gateway_id}/releases/programmable/deploy/ */
export interface IProgrammableDeployOutput {
  deploy_id: string
}
