import type { IGatewayRetrieveOutput, IGatewayUpdateInputSLZ } from '@/services/types/gateway/gateway.ts';

export type GatewayFormSource = Partial<Pick<IGatewayRetrieveOutput,
  'id' | 'name' | 'display_name' | 'description' | 'maintainers' | 'developers' | 'is_public' | 'kind'
  | 'extra_info' | 'bk_app_codes' | 'related_app_codes' | 'oauth2_app_enabled'
>>;

export const toGatewayFormData = (gateway: GatewayFormSource = {
  extra_info: {
    language: 'python',
    repository: '',
  },
}) => ({
  id: gateway.id,
  name: gateway.name ?? '',
  display_name: gateway.display_name ?? gateway.name ?? '',
  description: gateway.description ?? '',
  maintainers: [...(gateway.maintainers ?? [])],
  developers: gateway.developers?.slice(),
  is_public: gateway.is_public ?? true,
  oauth2_app_enabled: gateway.oauth2_app_enabled === true,
  kind: gateway.kind ?? 0,
  extra_info: { ...gateway.extra_info },
  bk_app_codes: gateway.bk_app_codes?.slice(),
  related_app_codes: gateway.related_app_codes?.slice(),
});

export const toGatewayUpdatePayload = (
  data: ReturnType<typeof toGatewayFormData>,
  saved: ReturnType<typeof toGatewayFormData>,
  appBindingEnabled: boolean,
) => {
  const { language, repository } = data.extra_info;
  const extraInfo: NonNullable<IGatewayUpdateInputSLZ['extra_info']> = {
    language: language === 'python' || language === 'go' || language === '' ? language : undefined,
    repository,
  };
  return {
    // 未修改时省略，避免覆盖后端返回的默认语言展示名。
    ...(data.display_name !== saved.display_name && { display_name: data.display_name }),
    ...(data.oauth2_app_enabled !== saved.oauth2_app_enabled && { oauth2_app_enabled: data.oauth2_app_enabled }),
    description: data.description,
    maintainers: data.maintainers,
    is_public: data.is_public,
    ...(data.developers && { developers: data.developers }),
    ...(appBindingEnabled && data.bk_app_codes && { bk_app_codes: data.bk_app_codes }),
    ...(data.related_app_codes && { related_app_codes: data.related_app_codes }),
    ...(data.kind === 1 && { extra_info: extraInfo }),
  } satisfies IGatewayUpdateInputSLZ;
};
