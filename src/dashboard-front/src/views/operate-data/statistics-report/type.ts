export interface SearchParamsType {
  stage_id: number;
  resource_id?: string;
  metrics: string;
  time_start?: number;
  time_end?: number;
  time_range?: string;
  limit?: number;
  offset?: number;
}

export interface SeriesItemType {
  alias: string;
  datapoints: Array<Array<number>>;
  dimensions: Object;
  metric_field: string;
  target: string;
  unit: string;
}

type ChartsSires = {
  metrics?: Array<unknown>;
  series?: Array<SeriesItemType>;
};

export interface ChartDataType {
  requests_total?: ChartsSires;
  requests?: ChartsSires;
  non_200_status?: ChartsSires;
  app_requests?: ChartsSires;
  resource_requests?: ChartsSires;
  ingress?: ChartsSires;
  egress?: ChartsSires;
  failed_500_requests?: ChartsSires;
  response_time?: ChartsSires;
}
