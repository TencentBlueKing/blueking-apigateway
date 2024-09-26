export interface SearchParamsType {
  stage_id: number;
  resource_id?: string;
  metrics: string;
  time_start?: number;
  time_end?: number;
  time_range?: string;
  limit?: number;
  offset?: number;
};
