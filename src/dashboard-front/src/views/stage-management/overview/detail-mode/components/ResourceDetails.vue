<template>
  <div class="release-sideslider">
    <BkSideslider
      v-model:is-show="isShow"
      :width="960"
      :title="`${t('资源详情')}【${info.name}】`"
      quick-close
      @hidden="emit('hidden')"
    >
      <template #default>
        <div class="sideslider-content">
          <p class="title mt-16px">
            {{ t('基本信息') }}
          </p>
          <BkContainer
            class="ag-kv-box"
            :col="14"
            :margin="6"
          >
            <BkRow v-if="isAIGateway">
              <BkCol :span="4">
                <label class="ag-key">{{ t('资源类型') }}:</label>
              </BkCol>
              <BkCol :span="10">
                <div class="ag-value">
                  <BkTag :theme="isModelProxy ? 'info' : 'default'">
                    {{ isModelProxy ? t('模型代理 API') : t('普通 API') }}
                  </BkTag>
                </div>
              </BkCol>
            </BkRow>

            <BkRow>
              <BkCol :span="4">
                <label class="ag-key">{{ t('资源名称') }}:</label>
              </BkCol>
              <BkCol :span="10">
                <div class="ag-value">
                  {{ currentSource.name }}
                </div>
              </BkCol>
            </BkRow>

            <BkRow>
              <BkCol :span="4">
                <label class="ag-key">{{ t('资源地址') }}:</label>
              </BkCol>
              <BkCol :span="10">
                <div class="ag-value">
                  {{ currentSource.path }}
                </div>
              </BkCol>
            </BkRow>

            <BkRow>
              <BkCol :span="4">
                <label class="ag-key">{{ t('描述') }}:</label>
              </BkCol>
              <BkCol :span="10">
                <div class="ag-value">
                  {{ currentSource.description || '--' }}
                </div>
              </BkCol>
            </BkRow>

            <BkRow>
              <BkCol :span="4">
                <label class="ag-key">{{ t('标签') }}:</label>
              </BkCol>
              <BkCol :span="10">
                <div class="ag-value tags">
                  <template v-if="currentSource.gateway_label_ids?.length">
                    <BkTag
                      v-for="tag in labels?.filter((label: IGatewayLabelItem) => {
                        if (currentSource.gateway_label_ids?.includes(label.id))
                          return true;
                      })"
                      :key="tag.id"
                    >
                      {{ tag.name }}
                    </BkTag>
                  </template>
                  <template v-else>
                    --
                  </template>
                </div>
              </BkCol>
            </BkRow>

            <BkRow>
              <BkCol :span="4">
                <label class="ag-key">{{ t('认证方式') }}:</label>
              </BkCol>
              <BkCol :span="10">
                <div class="ag-value">
                  {{ resourceAuthText }}
                </div>
              </BkCol>
            </BkRow>

            <!-- 只有打开“用户认证”才展示 oauth2 相关配置 -->
            <template v-if="authConfig.auth_verified_required">
              <!-- 2026.08.10 暂不支持 oauth2_public_client_enabled，先隐藏 -->
              <!--              <BkRow> -->
              <!--                <BkCol :span="4"> -->
              <!--                  <label class="ag-key">{{ t('OAuth2 公开客户端模式') }}:</label> -->
              <!--                </BkCol> -->
              <!--                <BkCol :span="10"> -->
              <!--                  <div class="ag-value"> -->
              <!--                    {{ authConfig.oauth2_public_client_enabled ? t('是') : t('否') }} -->
              <!--                  </div> -->
              <!--                </BkCol> -->
              <!--              </BkRow> -->
              <BkRow>
                <BkCol :span="4">
                  <label class="ag-key">{{ t('个人令牌') }}:</label>
                </BkCol>
                <BkCol :span="10">
                  <div class="ag-value">
                    {{ authConfig.oauth2_personal_client_enabled ? t('是') : t('否') }}
                  </div>
                </BkCol>
              </BkRow>
            </template>

            <BkRow>
              <BkCol :span="4">
                <label class="ag-key">{{ t('校验应用权限') }}:</label>
              </BkCol>
              <BkCol :span="10">
                <div class="ag-value">
                  {{ permRequiredText }}
                </div>
              </BkCol>
            </BkRow>

            <BkRow>
              <BkCol :span="4">
                <label class="ag-key">{{ t('是否公开') }}:</label>
              </BkCol>
              <BkCol :span="10">
                <div class="ag-value">
                  {{ currentSource?.is_public ? t('是') : t('否') }}
                  {{
                    currentSource?.allow_apply_permission
                      ? `(${t('允许申请权限')})`
                      : `(${t('不允许申请权限')})`
                  }}
                </div>
              </BkCol>
            </BkRow>
          </BkContainer>

          <p
            class="title mt-16px"
          >
            {{ t('请求配置') }}
          </p>
          <BkContainer
            class="ag-kv-box"
            :col="14"
            :margin="6"
          >
            <BkRow>
              <BkCol :span="4">
                <label class="ag-key">{{ t('请求方法') }}:</label>
              </BkCol>
              <BkCol :span="10">
                <div class="ag-value">
                  <BkTag :theme="getMethodsTheme(currentSource.method)">
                    {{ currentSource.method }}
                  </BkTag>
                </div>
              </BkCol>
            </BkRow>

            <BkRow>
              <BkCol :span="4">
                <label class="ag-key">{{ t('请求路径') }}:</label>
              </BkCol>
              <BkCol :span="10">
                <div class="ag-value">
                  {{ currentSource.path }}
                </div>
              </BkCol>
            </BkRow>

            <BkRow v-if="!isModelProxy">
              <BkCol :span="4">
                <label class="ag-key">{{ t('启用 Websocket') }}:</label>
              </BkCol>
              <BkCol :span="10">
                <div class="ag-value">
                  {{ currentSource.enable_websocket ? t('是') : t('否') }}
                </div>
              </BkCol>
            </BkRow>
          </BkContainer>

          <template v-if="!isModelProxy">
            <p class="title">
              {{ t('请求参数') }}
            </p>
            <div>
              <BkContainer
                v-if="isNoneSchema"
                class="ag-kv-box pb-24px"
                :col="14"
                :margin="6"
              >
                <BkRow class="mb-0!">
                  <BkCol :span="4">
                    <label class="ag-key invisible">
                      {{ t('请求方法') }}
                    </label>
                  </BkCol>
                  <BkCol :span="10">
                    <div class="ag-value">
                      {{ t('该资源无请求参数') }}
                    </div>
                  </BkCol>
                </BkRow>
              </BkContainer>
              <RequestParams
                v-else
                :detail="currentSource"
                readonly
              />
            </div>
          </template>

          <p class="title mt-16px">
            {{ isModelProxy ? t('模型服务配置') : t('后端配置') }}
          </p>
          <BkContainer
            class="ag-kv-box"
            :col="14"
            :margin="6"
          >
            <BkRow>
              <BkCol :span="4">
                <label class="ag-key">{{ isModelProxy ? t('模型服务') : t('后端配置') }}:</label>
              </BkCol>
              <BkCol :span="10">
                <div class="ag-value">
                  {{
                    currentSource?.proxy?.backend?.name
                  }}
                </div>
              </BkCol>
            </BkRow>

            <template v-if="!isModelProxy">
              <BkRow>
                <BkCol :span="4">
                  <label class="ag-key">{{ t('请求方法') }}:</label>
                </BkCol>
                <BkCol :span="10">
                  <div class="ag-value">
                    <BkTag :theme="getMethodsTheme(currentSource?.proxy?.config?.method)">
                      {{ currentSource?.proxy?.config?.method }}
                    </BkTag>
                  </div>
                </BkCol>
              </BkRow>

              <BkRow v-if="currentSource?.proxy?.config?.timeout !== 0">
                <BkCol :span="4">
                  <label class="ag-key">{{ t('自定义超时时间') }}:</label>
                </BkCol>
                <BkCol :span="10">
                  <div class="ag-value">
                    {{ currentSource?.proxy?.config?.timeout }}
                  </div>
                </BkCol>
              </BkRow>

              <BkRow>
                <BkCol :span="4">
                  <label class="ag-key">{{ t('请求路径') }}:</label>
                </BkCol>
                <BkCol :span="10">
                  <div class="ag-value">
                    {{
                      currentSource?.proxy?.config?.path
                    }}
                  </div>
                </BkCol>
              </BkRow>
            </template>
          </BkContainer>

          <template v-if="!isModelProxy">
            <p class="title">
              {{ t('响应参数') }}
            </p>
            <div>
              <ResponseParams
                v-if="Object.keys(currentSource.openapi_schema?.responses || {}).length"
                :detail="currentSource"
                readonly
              />
              <BkContainer
                v-else
                class="ag-kv-box pb-24px"
                :col="14"
                :margin="6"
              >
                <BkRow class="mb-0!">
                  <BkCol :span="4">
                    <label class="ag-key invisible">
                      {{ t('响应参数') }}
                    </label>
                  </BkCol>
                  <BkCol :span="10">
                    <div class="ag-value">
                      {{ t('该资源无响应参数') }}
                    </div>
                  </BkCol>
                </BkRow>
              </BkContainer>
            </div>
          </template>

          <p class="title mt-16px">
            {{ t('文档') }}
          </p>
          <BkContainer
            class="ag-kv-box"
            :col="14"
            :margin="6"
          >
            <BkRow>
              <BkCol :span="4">
                <label class="ag-key">{{ t('中文文档更新时间') }}:</label>
              </BkCol>
              <BkCol :span="10">
                <div class="ag-value">
                  {{ currentSource?.doc_updated_time?.zh || '--' }}
                </div>
              </BkCol>
            </BkRow>
            <BkRow>
              <BkCol :span="4">
                <label class="ag-key">{{ t('英文文档更新时间') }}:</label>
              </BkCol>
              <BkCol :span="10">
                <div class="ag-value">
                  {{ currentSource?.doc_updated_time?.en || '--' }}
                </div>
              </BkCol>
            </BkRow>
          </BkContainer>

          <template
            v-for="plugin in currentSource.plugins"
            :key="plugin.id"
          >
            <p class="title plugin-display">
              {{ t('插件') }}: {{ plugin.name }}
            </p>
            <ConfigDisplayTable :plugin="plugin" />
          </template>
        </div>
      </template>
    </BkSideslider>
  </div>
</template>

<script lang="ts" setup>
import { getGatewayLabels } from '@/services/source/gateway';
import { getMethodsTheme } from '@/utils';
import { useGateway } from '@/stores';
import type { IExtractApiReturn } from '@/services/types/utils.ts';
import ConfigDisplayTable from '@/components/plugin-manage/ConfigDisplayTable.vue';
import ResponseParams from '@/views/resource-management/components/response-params/Index.vue';
import RequestParams from '@/views/resource-management/components/request-params/Index.vue';

type IGatewayLabelItem = IExtractApiReturn<typeof getGatewayLabels>[number];

interface IAuthConfig {
  app_verified_required: boolean
  auth_verified_required: boolean
  resource_perm_required: boolean
  // oauth2_public_client_enabled: boolean
  oauth2_personal_client_enabled: boolean
}

interface IProps {
  info: any
}

const { info } = defineProps<IProps>();

const emit = defineEmits<{ hidden: [void] }>();

const { t } = useI18n();
const route = useRoute();
const gatewayStore = useGateway();

const isShow = ref(false);
const currentSource = ref<any>({});

// 网关标签
const labels = ref<IGatewayLabelItem[]>([]);

// 网关id
const apigwId = computed(() => +route.params.id);

const authConfig = computed<IAuthConfig>(() => {
  try {
    return JSON.parse(info.contexts?.resource_auth?.config);
  }
  catch {
    return {
      app_verified_required: false,
      auth_verified_required: false,
      resource_perm_required: false,
      // oauth2_public_client_enabled: false,
      oauth2_personal_client_enabled: false,
    };
  }
});

const resourceAuthText = computed(() => {
  const tmpArr: string[] = [];

  if (authConfig.value.app_verified_required) {
    tmpArr.push(`${t('应用认证')}`);
  }
  if (authConfig.value.auth_verified_required) {
    tmpArr.push(`${t('用户认证')}`);
  }
  return tmpArr.join(', ');
});

const permRequiredText = computed(() => authConfig.value.resource_perm_required ? t('校验') : t('不校验'));

const isAIGateway = computed(() => gatewayStore.isAIGateway);

const isModelProxy = computed(() => currentSource.value.kind === 'ai');

const isNoneSchema = computed(() =>
  !Object.keys(currentSource.value.openapi_schema ?? {})?.length || currentSource.value?.openapi_schema?.none_schema,
);

watch(
  () => info,
  () => {
    getInfo();
  },
);

// 获取详情数据
const getInfo = () => {
  if (!info) return;
  currentSource.value = info || {};
  if (currentSource.value?.proxy?.config) {
    if (typeof currentSource.value?.proxy?.config === 'string') {
      currentSource.value.proxy.config = JSON.parse(currentSource.value?.proxy?.config);
    }
    else {
      currentSource.value.proxy.config = {};
    }
  }
};
getInfo();

// 显示侧边栏
const showSideslider = () => {
  isShow.value = true;
};

const getLabels = async () => {
  labels.value = await getGatewayLabels(apigwId.value);
};
getLabels();

defineExpose({ showSideslider });

</script>

<style lang="scss" scoped>

.sideslider-content {
  width: 100%;
  padding: 24px 24px 12px;
  overflow-y: auto;
  box-sizing: border-box;

  .log-name {
    font-size: 12px;
    font-weight: 700;
    color: #63656e;
  }

  .title {
    padding-bottom: 10px;
    margin-bottom: 17px;
    font-size: 13px;
    font-weight: bold;
    color: #63656e;
    border-bottom: 1px solid #dcdee5;

    &.plugin-display {
      padding-bottom: 0;
      margin-top: 36px;
      margin-bottom: 6px;
      border-bottom: none;
    }
  }

  .ag-kv-box {

    .bk-grid-row {
      margin-bottom: 12px;
    }

    .ag-key {
      display: block;
      padding-right: 0;
      font-size: 14px;
      color: #63656e;
      text-align: right;
    }

    .ag-value {
      font-size: 14px;
      color: #313238;

      &.tags {
        display: flex;
        gap: 4px;
        flex-wrap: wrap;
      }
    }
  }
}
</style>

<style lang="scss">
.sideslider-rg-version-collapse .bk-collapse-source {

  .bk-collapse-header {
    background-color: #f0f1f5;
  }

  .bk-collapse-content {
    padding: 12px 0 24px;
  }
}
</style>
