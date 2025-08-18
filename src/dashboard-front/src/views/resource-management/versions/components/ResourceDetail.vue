/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */

<template>
  <div class="release-sideslider">
    <BkSideslider
      v-model:is-show="renderIsShow"
      :width="960"
      :title="`${t('资源详情')}【${info.version || ''}】`"
      quick-close
      @hidden="handleHidden"
    >
      <template #default>
        <BkLoading
          :loading="isLoading"
          color="#ffffff"
          :opacity="1"
        >
          <div class="sideslider-content">
            <div class="sideslider-lf">
              <BkInput
                v-model="keywords"
                class="mb-12px"
                type="search"
                clearable
              />
              <div class="sideslider-lf-ul">
                <template v-if="getResources?.length">
                  <div
                    v-for="item in getResources"
                    :key="item.name"
                    class="sideslider-lf-li"
                    :class="[
                      currentSource.name === item.name ? 'active' : '',
                    ]"
                    @click="() => changeCurrentSource(item)"
                  >
                    <BkOverflowTitle type="tips">
                      <span v-dompurify-html="renderTitle(item.name)" />
                    </BkOverflowTitle>
                  </div>
                </template>
                <BkException
                  v-else
                  class="exception-wrap-item exception-part"
                  :type="exceptionType"
                  scene="part"
                  :description="exceptionDesc"
                >
                  <div class="search-empty-tips">
                    {{ t('可以尝试 调整关键词 或') }}
                    <span
                      class="clear-search"
                      @click="handleClearSearch"
                    >
                      {{ t('清空搜索条件') }}
                    </span>
                  </div>
                </BkException>
              </div>
            </div>
            <div class="sideslider-rg">
              <div class="sideslider-rg-version-collapse">
                <BkCollapse
                  v-model="activeIndex"
                  header-icon="right-shape"
                  class="bk-collapse-source"
                >
                  <BkCollapsePanel
                    :name="1"
                    class="mb-12px"
                  >
                    <span class="log-name">{{ t("版本日志") }}</span>
                    <template #content>
                      <div class="pl-32px">
                        <p>{{ info.comment }}</p>
                      </div>
                    </template>
                  </BkCollapsePanel>
                  <BkCollapsePanel
                    v-for="(source, index) in info?.resources"
                    :key="source?.name"
                    :name="index + 2"
                    :class="`source-${source.name}`"
                    class="mb-12px"
                  >
                    <span>
                      <BkTag :theme="getMethodsTheme(source.method)">{{ source.method }}</BkTag>
                      <span class="log-name">{{ source.name }}</span>
                    </span>
                    <template #content>
                      <div class="sideslider-rg-content">
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
                                <BkTag theme="success">
                                  {{ source.name }}
                                </BkTag>
                              </div>
                            </BkCol>
                          </BkRow>

                          <BkRow>
                            <BkCol :span="4">
                              <label class="ag-key">{{ t("资源地址") }}:</label>
                            </BkCol>
                            <BkCol :span="10">
                              <div class="ag-value">
                                {{ source.path }}
                              </div>
                            </BkCol>
                          </BkRow>

                          <BkRow>
                            <BkCol :span="4">
                              <label class="ag-key">{{ t("描述") }}:</label>
                            </BkCol>
                            <BkCol :span="10">
                              <div class="ag-value">
                                {{ source.description }}
                              </div>
                            </BkCol>
                          </BkRow>

                          <BkRow>
                            <BkCol :span="4">
                              <label class="ag-key">{{ t("标签") }}:</label>
                            </BkCol>
                            <BkCol :span="10">
                              <div class="ag-value tags">
                                <template v-if="source.gateway_label_ids?.length">
                                  <BkTag
                                    v-for="tag in labels?.filter((label) => {
                                      if (source.gateway_label_ids?.includes(label.id))
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
                                    source?.contexts?.resource_auth?.config
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
                                    source?.contexts?.resource_auth?.config
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
                                {{ source?.is_public ? t("是") : t("否") }}
                                {{
                                  source?.allow_apply_permission
                                    ? `(${t("允许申请权限")})`
                                    : `(${t("不允许申请权限")})`
                                }}
                              </div>
                            </BkCol>
                          </BkRow>
                        </BkContainer>

                        <p class="title mt-15px">
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
                                <BkTag :theme="getMethodsTheme(source.method)">
                                  {{ source.method }}
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
                                {{ source.path }}
                              </div>
                            </BkCol>
                          </BkRow>

                          <BkRow>
                            <BkCol :span="4">
                              <label class="ag-key">{{ t("启用 WebSocket") }}:</label>
                            </BkCol>
                            <BkCol :span="10">
                              <div class="ag-value">
                                {{ source.enable_websocket ? t("是") : t("否") }}
                              </div>
                            </BkCol>
                          </BkRow>
                        </BkContainer>

                        <p class="title mt-15px">
                          {{ t("请求参数") }}
                        </p>
                        <div>
                          <BkContainer
                            v-if="!Object.keys(source.openapi_schema || {}).length || source.openapi_schema.none_schema"
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
                            :detail="source"
                            readonly
                          />
                        </div>

                        <template v-if="info.schema_version === '2.0'">
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
                                    source?.proxy?.backend?.name
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
                                  <BkTag :theme="getMethodsTheme(source?.proxy?.config?.method)">
                                    {{
                                      source?.proxy?.config?.method
                                    }}
                                  </BkTag>
                                </div>
                              </BkCol>
                            </BkRow>

                            <BkRow>
                              <BkCol :span="4">
                                <label class="ag-key">{{ t("自定义超时时间") }}:</label>
                              </BkCol>
                              <BkCol :span="10">
                                <div class="ag-value">
                                  {{
                                    source?.proxy?.config?.timeout
                                  }}
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
                                    source?.proxy?.config?.path
                                  }}
                                </div>
                              </BkCol>
                            </BkRow>
                          </BkContainer>

                          <p class="title mt-15px">
                            {{ t("响应参数") }}
                          </p>
                          <div>
                            <ResponseParams
                              v-if="Object.keys(source.openapi_schema?.responses || {}).length"
                              :detail="source"
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
                        </template>

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
                                <template v-if="localLanguage === 'en'">
                                  {{ source?.doc_updated_time?.en || "--" }}
                                </template>
                                <template v-else>
                                  {{ source?.doc_updated_time?.zh || "--" }}
                                </template>
                              </div>
                            </BkCol>
                          </BkRow>
                        </BkContainer>

                        <template v-if="info.schema_version === '2.0'">
                          <template
                            v-for="plugin in source.plugins"
                            :key="plugin.id"
                          >
                            <p class="title mt-15px">
                              {{ t("插件") }}: {{ plugin.name }}
                            </p>
                            <ConfigDisplayTable
                              :plugin="plugin"
                              first-col-width="auto"
                            />
                          </template>
                        </template>
                      </div>
                    </template>
                  </BkCollapsePanel>
                </BkCollapse>
              </div>
            </div>
          </div>
        </BkLoading>
      </template>
    </BkSideslider>
  </div>
</template>

<script lang="ts" setup>
import { getGatewayLabels } from '@/services/source/gateway.ts';
import { getVersionDetail } from '@/services/source/resource.ts';
import { getMethodsTheme } from '@/utils';
import ConfigDisplayTable from '@/components/plugin-manage/ConfigDisplayTable.vue';
import RequestParams from '../../components/request-params/Index.vue';
import ResponseParams from '../../components/response-params/Index.vue';
import { locale } from '@/locales';

interface IProps {
  id: number
  isShow: boolean
}

const { id, isShow } = defineProps<IProps>();

const emits = defineEmits<{ hidden: [void] }>();

const { t } = useI18n();
const route = useRoute();

const activeIndex = ref([1]);
const info = ref<any>({});
const currentSource = ref<any>({});

// 网关标签
const labels = ref<any[]>([]);

const exceptionType = ref('empty');
const exceptionDesc = ref(t('暂无数据'));
const keywords = ref('');
const renderIsShow = ref(false);
const isLoading = ref(false);

const localLanguage = locale || 'zh-cn';

// 网关id
const apigwId = computed(() => +route.params.id);

// 搜索
const getResources = computed(() => {
  if (keywords.value === '') {
    exceptionType.value = 'empty';
    exceptionDesc.value = t('暂无数据');
  }
  else {
    exceptionType.value = 'search-empty';
    exceptionDesc.value = t('搜索结果为空');
  }
  return info.value?.resources?.filter((item: any) => item.name?.includes(keywords.value));
});

watch(
  () => isShow,
  async (v: boolean) => {
    renderIsShow.value = v;
    if (v) {
      isLoading.value = true;
      await getInfo();
      isLoading.value = false;
    }
  },
);

// 获取详情数据
const getInfo = async () => {
  if (!id || !apigwId.value) return;

  const res = await getVersionDetail(apigwId.value, id);
  info.value = res;
  currentSource.value = res.resources[0] || {};

  activeIndex.value = [1];
  res?.resources?.forEach((item: any, index: number) => {
    activeIndex.value?.push(index + 2);

    if (item?.proxy?.config) {
      if (typeof item?.proxy?.config === 'string') {
        item.proxy.config = JSON.parse(item?.proxy?.config);
      }
      else {
        // item.proxy.config = {};
      }
    }
  });
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

const getLabels = async () => {
  labels.value = await getGatewayLabels(apigwId.value);
};
getLabels();

// 切换资源
const changeCurrentSource = (source: any) => {
  currentSource.value = source;

  const el = document.querySelector(`.source-${source.name}`);
  el?.scrollIntoView({
    behavior: 'smooth', // 平滑滚动
    block: 'start', // 元素顶部与视口顶部对齐
  });
};

const handleClearSearch = () => {
  keywords.value = '';
};

const renderTitle = (name: string) => {
  let showName = name;
  if (keywords.value) {
    const reg = new RegExp(`(${keywords.value})`, 'ig');
    showName = showName.replace(reg, '<i class="keyword ag-strong primary">$1</i>');
  }

  return showName;
};

const handleHidden = () => {
  emits('hidden');
};
</script>

<style lang="scss" scoped>
.mb8 {
  margin-bottom: 8px;
}

.mb12 {
  margin-bottom: 12px;
}

.sideslider-content {
  display: flex;
  width: 100%;
  align-items: flex-start;

  .sideslider-lf {
    width: 320px;
    height: calc(100vh - 52px);
    padding: 20px 16px 0;
    background-color: #f5f7fb;
    box-sizing: border-box;

    .sideslider-lf-title {
      padding: 8px 12px;
      font-size: 12px;
      color: #63656e;
      background-color: #fff;
      border-radius: 2px;
    }

    .sideslider-lf-ul {
      height: calc(100% - 94px);
      overflow-y: auto;

      .search-empty-tips {
        margin-top: 8px;
        font-size: 12px;
        color: #979ba5;

        .clear-search {
          color: #3a84ff;
          cursor: pointer;
        }
      }
    }

    .sideslider-lf-li {
      padding: 8px 12px;
      margin-bottom: 8px;
      font-size: 12px;
      color: #63656e;
      cursor: pointer;
      background: #fff;
      border: 1px solid #fff;
      border-radius: 2px;
      box-sizing: border-box;

      &:hover {
        border: 1px solid #3a84ff;
      }

      &.active {
        font-weight: 700;
        color: #3a84ff;
        border: 1px solid #3a84ff;
      }
    }
  }

  .sideslider-rg {
    height: calc(100vh - 52px);
    padding: 24px 24px 0;
    overflow-y: auto;
    box-sizing: border-box;
    flex: 1;

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
}
</style>

<style lang="scss">
.sideslider-rg-version-collapse .bk-collapse-source {

  .bk-collapse-header {
    height: 36px;
    font-size: 12px;
    font-weight: 700;
    line-height: 36px;
    color: #63656E;
    background-color: #f0f1f5;
  }

  .bk-collapse-content {
    padding: 12px 0 24px;
  }
}
</style>
