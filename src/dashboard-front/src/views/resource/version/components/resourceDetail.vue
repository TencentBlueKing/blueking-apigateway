<!-- eslint-disable vue/no-v-html -->

<template>
  <div class="release-sideslider">
    <bk-sideslider
      v-model:isShow="renderIsShow"
      :width="960"
      :title="`${$t('资源详情')}【${info.version}】`"
      quick-close
      @hidden="handleHidden"
    >
      <template #default>
        <bk-loading :loading="isLoading" color="#ffffff" opacity="1">
          <div class="sideslider-content">
            <div class="sideslider-lf">
              <bk-input class="mb12" type="search" clearable v-model="keywords" />
              <!-- <div class="sideslider-lf-title mb8">{{ $t("版本日志") }}</div> -->
              <div class="sideslider-lf-ul">
                <template v-if="getResources?.length">
                  <div
                    :class="[
                      'sideslider-lf-li',
                      'mb8',
                      currentSource.name === item.name ? 'active' : '',
                    ]"
                    v-for="item in getResources"
                    :key="item.name"
                    @click="changeCurrentSource(item)"
                  >
                    <bk-overflow-title type="tips">
                      <span v-html="renderTitle(item.name)"></span>
                    </bk-overflow-title>
                  </div>
                </template>
                <bk-exception
                  v-else
                  class="exception-wrap-item exception-part"
                  :type="exceptionType"
                  scene="part"
                  :description="exceptionDesc"
                >
                  <div class="search-empty-tips">
                    {{ t('可以尝试 调整关键词 或') }}
                    <span class="clear-search" @click="handleClearSearch()">
                      {{ t('清空搜索条件') }}
                    </span>
                  </div>
                </bk-exception>
              </div>
            </div>
            <div class="sideslider-rg">
              <div class="sideslider-rg-version-collapse">
                <bk-collapse
                  v-model="activeIndex"
                  header-icon="right-shape"
                  class="bk-collapse-source"
                >
                  <bk-collapse-panel :name="1">
                    <span><span class="log-name">{{ $t("版本日志") }}</span></span>
                    <!-- <template #header>
                    <div class="bk-collapse-header">
                      <right-shape v-show="!activeIndex.includes(1)" />
                      <angle-up-fill v-show="activeIndex.includes(1)" />
                      <span class="log-name">版本日志</span>
                    </div>
                  </template> -->
                    <template #content>
                      <div style="padding-left: 32px">
                        <p>{{ info.comment }}</p>
                      </div>
                    </template>
                  </bk-collapse-panel>
                  <bk-collapse-panel :name="2">
                    <span>
                      <bk-tag :theme="getMethodsTheme(currentSource.method)">{{ currentSource.method }}</bk-tag>
                      <span class="log-name">{{ currentSource.name }}</span>
                    </span>
                    <template #content>
                      <div class="sideslider-rg-content">
                        <p
                          class="title mt15"
                        >
                          {{ $t("基本信息") }}
                        </p>
                        <bk-container class="ag-kv-box" :col="14" :margin="6">
                          <bk-row>
                            <bk-col :span="4">
                              <label class="ag-key">{{ $t("资源名称") }}:</label>
                            </bk-col>
                            <bk-col :span="10">
                              <div class="ag-value">
                                <bk-tag theme="success">
                                  {{ currentSource.name }}
                                </bk-tag>
                              </div>
                            </bk-col>
                          </bk-row>

                          <bk-row>
                            <bk-col :span="4">
                              <label class="ag-key">{{ $t("资源地址") }}:</label>
                            </bk-col>
                            <bk-col :span="10">
                              <div class="ag-value">{{ currentSource.path }}</div>
                            </bk-col>
                          </bk-row>

                          <bk-row>
                            <bk-col :span="4">
                              <label class="ag-key">{{ $t("描述") }}:</label>
                            </bk-col>
                            <bk-col :span="10">
                              <div class="ag-value">{{ currentSource.description }}</div>
                            </bk-col>
                          </bk-row>

                          <bk-row>
                            <bk-col :span="4">
                              <label class="ag-key">{{ $t("标签") }}:</label>
                            </bk-col>
                            <bk-col :span="10">
                              <div class="ag-value">
                                <template v-if="currentSource.gateway_label_ids?.length">
                                  <bk-tag
                                    v-for="tag in labels?.filter((label) => {
                                      if (currentSource.gateway_label_ids?.includes(label.id))
                                        return true;
                                    })"
                                    :key="tag.id"
                                  >{{ tag.name }}</bk-tag
                                  >
                                </template>
                                <template v-else>
                                  --
                                </template>
                              </div>
                            </bk-col>
                          </bk-row>

                          <bk-row>
                            <bk-col :span="4">
                              <label class="ag-key">{{ $t("认证方式") }}:</label>
                            </bk-col>
                            <bk-col :span="10">
                              <div class="ag-value">
                                {{
                                  getResourceAuth(
                                    currentSource?.contexts?.resource_auth?.config
                                  )
                                }}</div>
                            </bk-col>
                          </bk-row>

                          <bk-row>
                            <bk-col :span="4">
                              <label class="ag-key">{{ $t("校验应用权限") }}:</label>
                            </bk-col>
                            <bk-col :span="10">
                              <div class="ag-value">
                                {{
                                  getPermRequired(
                                    currentSource?.contexts?.resource_auth?.config
                                  )
                                }}
                              </div>
                            </bk-col>
                          </bk-row>

                          <bk-row>
                            <bk-col :span="4">
                              <label class="ag-key">{{ $t("是否公开") }}:</label>
                            </bk-col>
                            <bk-col :span="10">
                              <div class="ag-value">
                                {{ currentSource?.is_public ? $t("是") : $t("否") }}
                                {{
                                  currentSource?.allow_apply_permission
                                    ? `(${ $t("允许申请权限") })`
                                    : `(${ $t("不允许申请权限") })`
                                }}
                              </div>
                            </bk-col>
                          </bk-row>
                        </bk-container>

                        <p
                          class="title mt15"
                        >
                          {{ $t("前端配置") }}
                        </p>
                        <bk-container class="ag-kv-box" :col="14" :margin="6">
                          <bk-row>
                            <bk-col :span="4">
                              <label class="ag-key">{{ $t("请求方法") }}:</label>
                            </bk-col>
                            <bk-col :span="10">
                              <div class="ag-value">
                                <bk-tag :theme="getMethodsTheme(currentSource.method)">
                                  {{ currentSource.method }}
                                </bk-tag>
                              </div>
                            </bk-col>
                          </bk-row>

                          <bk-row>
                            <bk-col :span="4">
                              <label class="ag-key">{{ $t("请求路径") }}:</label>
                            </bk-col>
                            <bk-col :span="10">
                              <div class="ag-value">{{ currentSource.path }}</div>
                            </bk-col>
                          </bk-row>
                        </bk-container>

                        <template v-if="info.schema_version === '2.0'">
                          <p
                            class="title mt15"
                          >
                            {{ $t("后端配置") }}
                          </p>
                          <bk-container class="ag-kv-box" :col="14" :margin="6">
                            <bk-row>
                              <bk-col :span="4">
                                <label class="ag-key">{{ $t("后端服务") }}:</label>
                              </bk-col>
                              <bk-col :span="10">
                                <div class="ag-value">
                                  {{
                                    currentSource?.proxy?.backend?.name
                                  }}
                                </div>
                              </bk-col>
                            </bk-row>

                            <bk-row>
                              <bk-col :span="4">
                                <label class="ag-key">{{ $t("请求方法") }}:</label>
                              </bk-col>
                              <bk-col :span="10">
                                <div class="ag-value">
                                  <bk-tag :theme="getMethodsTheme(currentSource?.proxy?.config?.method)">
                                    {{
                                      currentSource?.proxy?.config?.method
                                    }}
                                  </bk-tag>
                                </div>
                              </bk-col>
                            </bk-row>

                            <bk-row>
                              <bk-col :span="4">
                                <label class="ag-key">{{ $t("自定义超时时间") }}:</label>
                              </bk-col>
                              <bk-col :span="10">
                                <div class="ag-value">
                                  {{
                                    currentSource?.proxy?.config?.timeout
                                  }}
                                </div>
                              </bk-col>
                            </bk-row>

                            <bk-row>
                              <bk-col :span="4">
                                <label class="ag-key">{{ $t("请求路径") }}:</label>
                              </bk-col>
                              <bk-col :span="10">
                                <div class="ag-value">
                                  {{
                                    currentSource?.proxy?.config?.path
                                  }}
                                </div>
                              </bk-col>
                            </bk-row>
                          </bk-container>
                        </template>

                        <p
                          class="title mt15"
                        >
                          {{ $t("文档") }}
                        </p>
                        <bk-container class="ag-kv-box" :col="14" :margin="6">
                          <bk-row>
                            <bk-col :span="4">
                              <label class="ag-key">{{ $t("文档更新时间") }}:</label>
                            </bk-col>
                            <bk-col :span="10">
                              <div class="ag-value">
                                <template v-if="localLanguage === 'en'">
                                  {{ currentSource?.doc_updated_time?.en || "--" }}
                                </template>
                                <template v-else>
                                  {{ currentSource?.doc_updated_time?.zh || "--" }}
                                </template>
                              </div>
                            </bk-col>
                          </bk-row>
                        </bk-container>

                        <template v-if="info.schema_version === '2.0'">
                          <template v-for="plugin in currentSource.plugins" :key="plugin.id">
                            <p
                              class="title mt15"
                            >
                              {{ $t("插件") }}: {{ plugin.name }}
                            </p>
                            <bk-container class="ag-kv-box" :col="14" :margin="6">
                              <bk-row v-for="key in Object.keys(plugin.config)" :key="key">
                                <bk-col :span="4">
                                  <label class="ag-key">{{ key }}:</label>
                                </bk-col>
                                <bk-col :span="10">
                                  <div class="ag-value">
                                    {{ plugin.config[key] }}
                                  </div>
                                </bk-col>
                              </bk-row>
                            </bk-container>
                          </template>
                        </template>
                      </div>
                    </template>
                  </bk-collapse-panel>
                </bk-collapse>
              </div>
            </div>
          </div>
        </bk-loading>
      </template>
    </bk-sideslider>
  </div>
</template>

<script lang="ts" setup>
import { ref, watch, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import cookie from 'cookie';
// import { RightShape, AngleUpFill } from "bkui-vue/lib/icon";
import { getResourceVersionsInfo, getGatewayLabels } from '@/http';
import { getMethodsTheme } from '@/common/util';

const { t } = useI18n();
const route = useRoute();
// 网关id
const apigwId = computed(() => +route.params.id);
const localLanguage =  cookie.parse(document.cookie).blueking_language || 'zh-cn';

const props = defineProps<{
  id: number | undefined;
  isShow: boolean;
}>();

const emits = defineEmits<(event: 'hidden') => void>();

const activeIndex = ref([1, 2]);
const info = ref<any>({});
const currentSource = ref<any>({});

// 获取详情数据
const getInfo = async () => {
  if (!props.id || !apigwId.value) return;

  try {
    const res = await getResourceVersionsInfo(apigwId.value, props.id);
    console.log('res:  ', res);
    info.value = res;
    currentSource.value = res.resources[0] || {};
    if (currentSource.value?.proxy?.config) {
      if (typeof currentSource.value?.proxy?.config === 'string') {
        currentSource.value.proxy.config = JSON.parse(currentSource.value?.proxy?.config);
      } else {
        currentSource.value.proxy.config = {};
      }
    }
  } catch (e) {
    console.log(e);
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

// 网关标签
const labels = ref<any[]>([]);
const getLabels = async () => {
  try {
    const res = await getGatewayLabels(apigwId.value);
    labels.value = res;
  } catch (e) {
    console.log(e);
  }
};
getLabels();

// 切换资源
const changeCurrentSource = (source: any) => {
  currentSource.value = source;
  if (currentSource.value?.proxy?.config) {
    if (typeof currentSource.value?.proxy?.config === 'string') {
      currentSource.value.proxy.config = JSON.parse(currentSource.value?.proxy?.config);
    } else {
      currentSource.value.proxy.config = {};
    }
  }
};

const exceptionType = ref('empty');
const exceptionDesc = ref(t('暂无数据'));

const keywords = ref('');
// 搜索
const getResources = computed(() => {
  if (keywords.value === '') {
    exceptionType.value = 'empty';
    exceptionDesc.value = t('暂无数据');
  } else {
    exceptionType.value = 'search-empty';
    exceptionDesc.value = t('搜索结果为空');
  }
  return info.value?.resources?.filter((item: any) => item.name?.includes(keywords.value));
});

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

const renderIsShow = ref(false);

const handleHidden = () => {
  emits('hidden');
};

const isLoading = ref(false);

watch(
  () => props.isShow,
  async (v: boolean) => {
    renderIsShow.value = v;
    if (v) {
      isLoading.value = true;
      await getInfo();
      isLoading.value = false;
    }
  },
);
</script>

<style lang="scss" scoped>
.mb8 {
  margin-bottom: 8px;
}
.mb12 {
  margin-bottom: 12px;
}
.sideslider-content {
  width: 100%;
  display: flex;
  align-items: flex-start;
  .sideslider-lf {
    width: 320px;
    background-color: #f5f7fb;
    height: calc(100vh - 52px);
    padding: 20px 16px 0px;
    box-sizing: border-box;
    .sideslider-lf-title {
      background-color: #ffffff;
      color: #63656e;
      padding: 8px 12px;
      border-radius: 2px;
      font-size: 12px;
    }
    .sideslider-lf-ul {
      height: calc(100% - 94px);
      overflow-y: scroll;
      .search-empty-tips {
        font-size: 12px;
        margin-top: 8px;
        color: #979ba5;

        .clear-search {
            cursor: pointer;
            color: #3a84ff;
        }
      }
    }
    .sideslider-lf-li {
      cursor: pointer;
      background: #ffffff;
      border-radius: 2px;
      padding: 8px 12px;
      color: #63656e;
      font-size: 12px;
      box-sizing: border-box;
      border: 1px solid #ffffff;
      &:hover {
        border: 1px solid #3a84ff;
      }
      &.active {
        border: 1px solid #3a84ff;
        color: #3a84ff;
        font-weight: 700;
      }
    }
  }
  .sideslider-rg {
    flex: 1;
    padding: 24px 24px 0px;
    box-sizing: border-box;
    height: calc(100vh - 52px);
    overflow-y: scroll;
    .log-name {
      font-size: 12px;
      color: #63656e;
      font-weight: 700;
    }
    .title {
      font-size: 13px;
      color: #63656e;
      font-weight: bold;
      padding-bottom: 10px;
      border-bottom: 1px solid #dcdee5;
      margin-bottom: 17px;
    }
    .ag-kv-box {
      .bk-grid-row {
        margin-bottom: 12px;
      }
      .ag-key {
        font-size: 14px;
        color: #63656e;
        display: block;
        text-align: right;
        padding-right: 0;
      }

      .ag-value {
        font-size: 14px;
        color: #313238;
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
    padding: 12px 0px 24px;
  }
}
</style>
