// POST /esb/components/
export interface IEsbComponentsCreate {
  system_id: number
  system_name?: string
  name: string
  description: string
  method: '' | 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  path: string
  component_codename: string
  permission_level: 'unlimited' | 'normal' | 'sensitive' | 'special'
  verified_user_required?: boolean | null
  timeout?: number | null
  config?: Record<string, string | null>
  is_active?: boolean
  api_url?: string
  doc_link?: string
  is_official?: boolean
  updated_time?: string | null
  is_created?: string
  has_updated?: string
}

// POST /esb/doc-categories/
export interface IEsbDocCategoriesCreate {
  name: string
  priority?: number
  is_official?: boolean
  updated_time?: string | null
  system_count?: number
}

// POST /esb/systems/
export interface IEsbSystemsCreate {
  name: string
  description: string
  description_en?: string | null
  comment?: string
  timeout?: number | null
  maintainers: string[]
  doc_category_id: number
  doc_category_name?: string
  component_count?: number
  is_official?: boolean
}
