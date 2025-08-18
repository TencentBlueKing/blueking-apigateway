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
          <p class="title mt-15px">
            {{ t("基本信息") }}
          </p>
          <BkContainer
            class="ag-kv-box"
            :col="14"
            :margin="6"
          >
            <BkRow>
              <BkCol :span="4">
                <label class="ag-key">{{ t("资源名称") }}:</label>
              </BkCol>
              <BkCol :span="10">
                <div class="ag-value">
                  {{ currentSource.name }}
                </div>
              </BkCol>
            </BkRow>

            <BkRow>
              <BkCol :span="4">
                <label class="ag-key">{{ t("资源地址") }}:</label>
              </BkCol>
              <BkCol :span="10">
                <div class="ag-value">
                  {{ currentSource.path }}
                </div>
              </BkCol>
            </BkRow>

            <BkRow>
              <BkCol :span="4">
                <label class="ag-key">{{ t("描述") }}:</label>
              </BkCol>
              <BkCol :span="10">
                <div class="ag-value">
                  {{ currentSource.description }}
                </div>
              </BkCol>
            </BkRow>

            <BkRow>
              <BkCol :span="4">
                <label class="ag-key">{{ t("标签") }}:</label>
              </BkCol>
              <BkCol :span="10">
                <div class="ag-value tags">
                  <template v-if="currentSource.gateway_label_ids?.length">
                    <BkTag
                      v-for="tag in labels?.filter((label) => {
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
                <label class="ag-key">{{ t("认证方式") }}:</label>
              </BkCol>
              <BkCol :span="10">
                <div class="ag-value">
                  {{
                    getResourceAuth(
                      currentSource?.contexts?.resource_auth?.config
                    )
                  }}
                </div>
              </BkCol>
            </BkRow>

            <BkRow>
              <BkCol :span="4">
                <label class="ag-key">{{ t("校验应用权限") }}:</label>
              </BkCol>
              <BkCol :span="10">
                <div class="ag-value">
                  {{
                    getPermRequired(
                      currentSource?.contexts?.resource_auth?.config
                    )
                  }}
                </div>
              </BkCol>
            </BkRow>

            <BkRow>
              <BkCol :span="4">
                <label class="ag-key">{{ t("是否公开") }}:</label>
              </BkCol>
              <BkCol :span="10">
                <div class="ag-value">
                  {{ currentSource?.is_public ? t("是") : t("否") }}
                  {{
                    currentSource?.allow_apply_permission
                      ? `(${t("允许申请权限")})`
                      : `(${t("不允许申请权限")})`
                  }}
                </div>
              </BkCol>
            </BkRow>
          </BkContainer>

          <p
            class="title mt-15px"
          >
            {{ t("请求配置") }}
          </p>
          <BkContainer
            class="ag-kv-box"
            :col="14"
            :margin="6"
          >
            <BkRow>
              <BkCol :span="4">
                <label class="ag-key">{{ t("请求方法") }}:</label>
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
                <label class="ag-key">{{ t("请求路径") }}:</label>
              </BkCol>
              <BkCol :span="10">
                <div class="ag-value">
                  {{ currentSource.path }}
                </div>
              </BkCol>
            </BkRow>

            <BkRow>
              <BkCol :span="4">
                <label class="ag-key">{{ t("启用 Websocket") }}:</label>
              </BkCol>
              <BkCol :span="10">
                <div class="ag-value">
                  {{ currentSource.enable_websocket ? t('是') : t('否') }}
                </div>
              </BkCol>
            </BkRow>
          </BkContainer>

          <p class="title">
            {{ t('请求参数') }}
          </p>
          <div>
            <BkContainer
              v-if="!Object.keys(currentSource.openapi_schema || {}).length || currentSource.openapi_schema.none_schema"
              class="ag-kv-box pb-24px"
              :col="14"
              :margin="6"
            >
              <BkRow class="mb-0!">
                <BkCol :span="4">
                  <label class="ag-key invisible">
                    {{ t("请求方法") }}
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

          <p class="title mt-15px">
            {{ t("后端配置") }}
          </p>
          <BkContainer
            class="ag-kv-box"
            :col="14"
            :margin="6"
          >
            <BkRow>
              <BkCol :span="4">
                <label class="ag-key">{{ t("后端服务") }}:</label>
              </BkCol>
              <BkCol :span="10">
                <div class="ag-value">
                  {{
                    currentSource?.proxy?.backend?.name
                  }}
                </div>
              </BkCol>
            </BkRow>

            <BkRow>
              <BkCol :span="4">
                <label class="ag-key">{{ t("请求方法") }}:</label>
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
                <label class="ag-key">{{ t("自定义超时时间") }}:</label>
              </BkCol>
              <BkCol :span="10">
                <div class="ag-value">
                  {{ currentSource?.proxy?.config?.timeout }}
                </div>
              </BkCol>
            </BkRow>

            <BkRow>
              <BkCol :span="4">
                <label class="ag-key">{{ t("请求路径") }}:</label>
              </BkCol>
              <BkCol :span="10">
                <div class="ag-value">
                  {{
                    currentSource?.proxy?.config?.path
                  }}
                </div>
              </BkCol>
            </BkRow>
          </BkContainer>

          <p class="title">
            {{ t("响应参数") }}
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
                    {{ t("响应参数") }}
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

          <p class="title mt-15px">
            {{ t("文档") }}
          </p>
          <BkContainer
            class="ag-kv-box"
            :col="14"
            :margin="6"
          >
            <BkRow>
              <BkCol :span="4">
                <label class="ag-key">{{ t("文档更新时间") }}:</label>
              </BkCol>
              <BkCol :span="10">
                <div class="ag-value">
                  <template v-if="locale === 'en'">
                    {{ currentSource?.doc_updated_time?.en || "--" }}
                  </template>
                  <template v-else>
                    {{ currentSource?.doc_updated_time?.zh || "--" }}
                  </template>
                </div>
              </BkCol>
            </BkRow>
          </BkContainer>

          <template
            v-for="plugin in currentSource.plugins"
            :key="plugin.id"
          >
            <p class="title plugin-display">
              {{ t("插件") }}: {{ plugin.name }}
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
import ConfigDisplayTable from '@/components/plugin-manage/ConfigDisplayTable.vue';
import ResponseParams from '@/views/resource-management/components/response-params/Index.vue';
import RequestParams from '@/views/resource-management/components/request-params/Index.vue';

interface IProps { info: any }

const { info } = defineProps<IProps>();

const emit = defineEmits<{ hidden: [void] }>();

const { t, locale } = useI18n();
const route = useRoute();

const isShow = ref(false);
const currentSource = ref<any>({});

// 网关标签
const labels = ref<any[]>([]);

// 网关id
const apigwId = computed(() => +route.params.id);

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

const getResourceAuth = (authStr: string) => {
  if (!authStr) return '';

  const auth = JSON.parse(authStr);
  const tmpArr: string[] = [];

  if (auth?.auth_verified_required) {
    tmpArr.push(`${t('用户认证')}`);
  }
  if (auth?.app_verified_required) {
    tmpArr.push(`${t('蓝鲸应用认证')}`);
  }
  return tmpArr.join(', ');
};

const getPermRequired = (authStr: string) => {
  if (!authStr) return '';

  const auth = JSON.parse(authStr);
  if (auth?.resource_perm_required) {
    return `${t('校验')}`;
  }
  return `${t('不校验')}`;
};

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
