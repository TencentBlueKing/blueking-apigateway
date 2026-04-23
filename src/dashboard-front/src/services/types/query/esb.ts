// GET /esb/components/
export interface IEsbComponentsListQuery {
  limit?: number
  offset?: number
  path?: string
  name?: string
  system_name?: string
}

// GET /esb/components/sync/release/histories/
export interface IEsbComponentsSyncReleaseHistoriesListQuery {
  limit?: number
  offset?: number
  time_start?: number | null
  time_end?: number | null
}

// GET /esb/doc-categories/
export interface IEsbDocCategoriesListQuery {
  limit?: number
  offset?: number
}

// GET /esb/systems/
export interface IEsbSystemsListQuery {
  limit?: number
  offset?: number
}
