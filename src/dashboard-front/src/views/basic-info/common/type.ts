export interface BasicInfoParams {
  name: string
  url?: string
  description?: string
  description_en?: string
  public_key_fingerprint?: string
  bk_app_codes: string
  related_app_codes: string
  docs_url: string
  api_domain?: string
  developers?: string[]
  maintainers?: string[]
  status?: number,
  is_public?: boolean
  created_by: string
  created_time: string
  public_key: string
  is_official: boolean
  publish_validate_msg?: string
  kind?: number
  extra_info?: {
    [key: string]: string
  }
}

export interface DialogParams {
  isShow: boolean,
  loading: boolean
  title?: string
}
