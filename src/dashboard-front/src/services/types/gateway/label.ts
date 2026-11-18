/** /gateways/{gateway_id}/labels/ [GET] */
export interface IGatewaysLabelsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

// POST /gateways/{gateway_id}/labels/ - 新建网关标签
export interface IGatewayLabelInputSLZ {
  id?: number
  name: string
}

/**
 * GET /gateways/{gateway_id}/labels/
 */
export interface IGatewayLabelOutput {
  id: number
  name: string
}
