import type { IAIBackendConfigInput, IAIBackendConfigOutput } from '@/services/types/gateway/backend.ts';

/** /gateways/{gateway_id}/stages/ [GET] */
export interface IGatewaysStagesListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

/** /gateways/{gateway_id}/stages/{id}/backends/ [GET] */
export interface IGatewaysStagesBackendsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

interface IStageStandardBackendConfigInput {
  type?: string
  timeout: number
  loadbalance: string
  hash_on?: string
  key?: string
  hosts: {
    scheme: string
    host: string
    weight?: number
  }[]
  checks?: {
    active?: {
      type?: string
      timeout?: number
      concurrency?: number
      http_path?: string
      https_verify_certificate?: boolean
      healthy?: {
        http_statuses?: number[]
        successes?: number
        interval?: number
      }
      unhealthy?: {
        http_statuses?: number[]
        http_failures?: number
        tcp_failures?: number
        timeouts?: number
        interval?: number
      }
    }
    passive?: {
      type?: string
      healthy?: {
        http_statuses?: number[]
        successes?: number
      }
      unhealthy?: {
        http_statuses?: number[]
        http_failures?: number
        tcp_failures?: number
        timeouts?: number
      }
    }
  }
}

type IStageAIBackendConfigInput = Omit<IAIBackendConfigInput, 'stage_id'>;

// POST /gateways/{gateway_id}/stages/ - 创建环境
export interface IStageInputSLZ {
  name: string
  description?: string
  backends: {
    id: number
    config: IStageStandardBackendConfigInput | IStageAIBackendConfigInput
  }[]
}

// PUT /gateways/{gateway_id}/stages/{id}/status/
export interface IStageStatusInputSLZ {
  status: number // 状态
}

// PUT /gateways/{gateway_id}/stages/{id}/vars/
export interface IStageVarsSLZ {
  vars?: Record<string, string>
}

/**
 * GET /gateways/{gateway_id}/stages/
 */
export interface IStageListOutput {
  id: number
  name: string
  description: string | null
  description_en: string | null
  status: number
  created_time: string | null
  release: {
    status: string
    created_time: string
    created_by: string
  }
  resource_version: {
    id: number
    version: string
    schema_version: string
  }
  publish_id: number
  publish_version: string
  publish_validate_msg: string
  new_resource_version: string
}

/**
 * GET /gateways/{gateway_id}/stages/{id}/
 */
export interface IStageRetrieveOutput {
  id: number
  name: string
  description: string | null
  description_en: string | null
  status: number
  created_time: string | null
  release: {
    status: string
    created_time: string
    created_by: string
  }
  resource_version: {
    id: number
    version: string
    schema_version: string
  }
  publish_id: number
  publish_version: string
  publish_validate_msg: string
  new_resource_version: string
}

interface IStandardStageBackendConfigOutput {
  type?: string
  timeout: number
  loadbalance: string
  hash_on?: string
  key?: string
  hosts: {
    scheme: string
    host: string
    weight?: number
  }[]
  checks?: {
    active?: {
      type?: string
      timeout?: number
      concurrency?: number
      http_path?: string
      https_verify_certificate?: boolean
      healthy?: {
        http_statuses?: number[]
        successes?: number
        interval?: number
      }
      unhealthy?: {
        http_statuses?: number[]
        http_failures?: number
        tcp_failures?: number
        timeouts?: number
        interval?: number
      }
    }
    passive?: {
      type?: string
      healthy?: {
        http_statuses?: number[]
        successes?: number
      }
      unhealthy?: {
        http_statuses?: number[]
        http_failures?: number
        tcp_failures?: number
        timeouts?: number
      }
    }
  }
}

type IAIStageBackendConfigOutput = Omit<IAIBackendConfigOutput, 'stage'>;

/**
 * GET /gateways/{gateway_id}/stages/{id}/backends/
 */
export interface IStageBackendListOutput {
  id: number
  name: string
  kind: string
  config: IStandardStageBackendConfigOutput | IAIStageBackendConfigOutput
}

/**
 * GET /gateways/{gateway_id}/stages/{id}/vars/
 */
export interface IStageVarsOutput {
  vars: {
    [key: string]: string
  }
}
