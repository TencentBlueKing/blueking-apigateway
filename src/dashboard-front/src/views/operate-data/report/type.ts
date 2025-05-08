export interface SearchParamsType {
  stage_id?: number;
  resource_id?: string;
  bk_app_code?: string;
  metrics?: string;
  time_dimension?: string;
  time_start?: number;
  time_end?: number;
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

export interface ChartDataLoading {
  requests_total?: boolean;
  requests_failed_total?: boolean;
}
