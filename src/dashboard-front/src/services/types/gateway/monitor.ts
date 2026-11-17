/** /gateways/{gateway_id}/monitors/alarm/records/ [GET] */
export interface IGatewaysMonitorsAlarmRecordsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 开始时间（Unix 秒）；只有起止都传才过滤，闭区间 created_time ∈ [time_start, time_end] */
  time_start?: number | null
  /** 结束时间（Unix 秒） */
  time_end?: number | null
  /** 告警策略 id */
  alarm_strategy_id?: number | null
  /** 告警状态 */
  status?: 'received' | 'skipped' | 'success' | 'failure'
}

/** /gateways/{gateway_id}/monitors/alarm/strategies/ [GET] */
export interface IGatewaysMonitorsAlarmStrategiesListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 查询关键字 */
  keyword?: string
  /** 网关标签 id */
  gateway_label_id?: number | null
  /** 排序字段 */
  order_by?: 'name' | '-name' | 'updated_time' | '-updated_time'
}

// PATCH /gateways/{gateway_id}/monitors/alarm/strategies/{id}/status/ - 更新告警策略状态
export interface IAlarmStrategyUpdateStatusInputSLZ {
  enabled?: boolean
}

// POST /gateways/{gateway_id}/monitors/alarm/strategies/ - 创建告警策略
export interface IAlarmStrategyInputSLZ {
  id?: number
  name: string
  alarm_type: string
  alarm_subtype: string
  gateway_label_ids: number[]
  config: {
    detect_config: {
      duration: number
      method: string
      count: number
    }
    converge_config: {
      duration: number
    }
    notice_config: {
      notice_way: string[]
      notice_role: string[]
      notice_extra_receiver: string[]
    }
  }
  effective_stages?: string[]
}

/**
 * GET /gateways/{gateway_id}/monitors/alarm/records/
 */
export interface IAlarmRecordListOutput {
  id: number
  alarm_id: string
  status: string
  message: string
  created_time: string
  alarm_strategy_names: string
  comment: string
}

/**
 * GET /gateways/{gateway_id}/monitors/alarm/strategies/
 */
export interface IAlarmStrategyListOutput {
  id: number
  name: string
  alarm_type: string
  alarm_subtype: string
  enabled: boolean
  updated_time: string | null
  gateway_labels: string
  effective_stages: string
}

/**
 * GET /gateways/{gateway_id}/monitors/alarm/strategies/{id}/
 */
export interface IAlarmStrategyRetrieveOutput {
  id: number
  name: string
  alarm_type: string
  alarm_subtype: string
  enabled: boolean
  updated_time: string | null
  gateway_labels: string
  effective_stages: string
}
