<template>
  <div
    v-if="curResource"
    class="ag-resource-item"
    :class="{ 'show-diff': onlyShowDiff }"
  >
    <p
      class="title"
      :class="{
        'ag-diff':
          checkDiff('localData.name') ||
          checkDiff('localData.path') ||
          checkDiff('localData.description') ||
          checkDiff('localData.api_labels') ||
          checkDiff(
            'localData.contexts.resource_auth.config.auth_verified_required'
          ) ||
          checkDiff(
            'localData.contexts.resource_auth.config.app_verified_required'
          ) ||
          checkDiff('localData.is_public') ||
          checkDiff(
            'localData.contexts.resource_auth.config.resource_perm_required'
          ) ||
          checkDiff('localData.is_public') ||
          checkDiff('localData.allow_apply_permission'),
      }"
    >
      {{ t("基本信息") }}
    </p>
    <BkContainer
      class="ag-kv-box"
      :col="14"
      :margin="6"
    >
      <BkRow :class="{ 'ag-diff': checkDiff('localData.name') }">
        <BkCol :span="4">
          <label class="ag-key">{{ t("资源名称") }}:</label>
        </BkCol>
        <BkCol :span="10">
          <div class="ag-value">
            {{ localData.name || "--" }}
          </div>
        </BkCol>
      </BkRow>

      <BkRow :class="{ 'ag-diff': checkDiff('localData.path') }">
        <BkCol :span="4">
          <label class="ag-key">{{ t("资源地址") }}:</label>
        </BkCol>
        <BkCol :span="10">
          <div class="ag-value">
            {{ localData.path || "--" }}
          </div>
        </BkCol>
      </BkRow>

      <BkRow :class="{ 'ag-diff': checkDiff('localData.description') }">
        <BkCol :span="4">
          <label class="ag-key">{{ t("描述") }}:</label>
        </BkCol>
        <BkCol :span="10">
          <div class="ag-value">
            {{ localData.description || "--" }}
          </div>
        </BkCol>
      </BkRow>

      <BkRow :class="{ 'ag-diff': checkDiff('localData.api_labels') }">
        <BkCol :span="4">
          <label class="ag-key">{{ t("标签") }}:</label>
        </BkCol>
        <BkCol
          style="margin-bottom: -4px;"
          :span="10"
        >
          <template v-if="localData.api_labels?.length">
            <BkTag
              v-for="tag in labels?.filter((label) =>
                localData.api_labels?.includes(label.id) || localData.api_labels?.includes(String(label.id)))"
              :key="tag.id"
              class="ag-value mb-4px ml-4px"
            >
              {{ tag.name }}
            </BkTag>
          </template>
          <div
            v-else
            class="ag-value"
          >
            --
          </div>
        </BkCol>
      </BkRow>

      <BkRow
        :class="{
          'ag-diff':
            checkDiff(
              'localData.contexts.resource_auth.config.auth_verified_required'
            ) ||
            checkDiff(
              'localData.contexts.resource_auth.config.app_verified_required'
            ),
        }"
      >
        <BkCol :span="4">
          <label class="ag-key">{{ t("认证方式") }}:</label>
        </BkCol>
        <BkCol :span="10">
          <div class="ag-value">
            {{ getResourceAuth(localData.contexts.resource_auth.config) }}
          </div>
        </BkCol>
      </BkRow>

      <BkRow
        :class="{
          'ag-diff': checkDiff(
            'localData.contexts.resource_auth.config.resource_perm_required'
          ),
        }"
      >
        <BkCol :span="4">
          <label class="ag-key">{{ t("校验应用权限") }}:</label>
        </BkCol>
        <BkCol :span="10">
          <div class="ag-value">
            {{
              localData.contexts.resource_auth.config.resource_perm_required
                ? t("校验")
                : t("不校验")
            }}
          </div>
        </BkCol>
      </BkRow>

      <BkRow
        :class="{
          'ag-diff':
            checkDiff('localData.is_public') ||
            checkDiff('localData.allow_apply_permission'),
        }"
      >
        <BkCol :span="4">
          <label class="ag-key">{{ t("是否公开") }}:</label>
        </BkCol>
        <BkCol :span="10">
          <div class="ag-value">
            {{ localData.is_public ? t("是") : t("否") }}
            {{
              localData.allow_apply_permission
                ? `(${t("允许申请权限")})`
                : `(${t("不允许申请权限")})`
            }}
          </div>
        </BkCol>
      </BkRow>
    </BkContainer>

    <p
      class="title mt-15px"
      :class="{
        'ag-diff': checkDiff('localData.method') || checkDiff('localData.path'),
      }"
    >
      {{ t("请求配置") }}
    </p>
    <BkContainer
      class="ag-kv-box"
      :col="14"
      :margin="6"
    >
      <BkRow :class="{ 'ag-diff': checkDiff('localData.method') }">
        <BkCol :span="4">
          <label class="ag-key">{{ t("请求方法") }}:</label>
        </BkCol>
        <BkCol :span="10">
          <div class="ag-value">
            {{ localData.method }}
          </div>
        </BkCol>
      </BkRow>

      <BkRow :class="{ 'ag-diff': checkDiff('localData.path') }">
        <BkCol :span="4">
          <label class="ag-key">{{ t("请求路径") }}:</label>
        </BkCol>
        <BkCol :span="10">
          <div class="ag-value">
            {{ localData.path }}
          </div>
        </BkCol>
      </BkRow>

      <BkRow :class="{ 'ag-diff': checkDiff('localData.match_subpath') }">
        <BkCol :span="4">
          <label class="ag-key">{{ t("匹配所有子路径") }}:</label>
        </BkCol>
        <BkCol :span="10">
          <div class="ag-value">
            {{ localData.match_subpath ? t("是") : t("否") }}
          </div>
        </BkCol>
      </BkRow>

      <BkRow :class="{ 'ag-diff': checkDiff('localData.enable_websocket') }">
        <BkCol :span="4">
          <label class="ag-key">{{ t("启用 WebSocket") }}:</label>
        </BkCol>
        <BkCol :span="10">
          <div class="ag-value">
            {{ localData.enable_websocket ? t("是") : t("否") }}
          </div>
        </BkCol>
      </BkRow>
    </BkContainer>

    <p
      :class="{
        'ag-diff': checkDiff('localData.openapi_schema'),
      }"
      class="title mt-15px"
    >
      {{ t("请求/响应参数") }}
    </p>
    <BkContainer
      :col="14"
      :margin="6"
      class="ag-kv-box"
    >
      <BkRow :class="{ 'ag-diff': checkDiff('localData.openapi_schema') }">
        <BkCol :span="4">
          <label class="ag-key">&nbsp;</label>
        </BkCol>
        <BkCol :span="10">
          <div class="ag-value">
            {{ isSource ? '--' : (checkDiff('localData.openapi_schema') ? t('有更新') : '--') }}
          </div>
        </BkCol>
      </BkRow>
    </BkContainer>

    <template v-if="localData.proxy?.backend_id">
      <p
        class="title mt-15px"
        :class="{
          'ag-diff':
            checkDiff('localData.proxy.backend_name') ||
            checkDiff('localData.proxy.config.method') ||
            checkDiff('localData.proxy.config.timeout') ||
            checkDiff('localData.proxy.config.path'),
        }"
      >
        {{ t("后端配置") }}
      </p>
      <BkContainer
        class="ag-kv-box"
        :col="14"
        :margin="6"
        :class="{ 'box-diff': checkDiff('localData.proxy.type') }"
      >
        <BkRow
          :class="{ 'ag-diff': checkDiff('localData.proxy.backend_name') }"
        >
          <BkCol :span="4">
            <label class="ag-key">{{ t("后端服务:") }}</label>
          </BkCol>
          <BkCol :span="10">
            <div class="ag-value">
              {{ localData.proxy.backend_name || "--" }}
            </div>
          </BkCol>
        </BkRow>

        <template v-if="localData.proxy.type === 'http'">
          <BkRow
            :class="{ 'ag-diff': checkDiff('localData.proxy.config.method') }"
          >
            <BkCol :span="4">
              <label class="ag-key">{{ t("请求方法") }}:</label>
            </BkCol>
            <BkCol :span="10">
              <div class="ag-value">
                {{ localData.proxy.config.method || "--" }}
              </div>
            </BkCol>
          </BkRow>

          <BkRow
            :class="{
              'ag-diff': checkDiff('localData.proxy.config.timeout'),
            }"
          >
            <BkCol :span="4">
              <label class="ag-key">{{ t("自定义超时时间:") }}</label>
            </BkCol>
            <BkCol :span="10">
              <div class="ag-value">
                {{ localData.proxy.config.timeout }}
              </div>
            </BkCol>
          </BkRow>

          <BkRow
            :class="{ 'ag-diff': checkDiff('localData.proxy.config.path') }"
          >
            <BkCol :span="4">
              <label class="ag-key">{{ t("请求路径:") }}</label>
            </BkCol>
            <BkCol :span="10">
              <div class="ag-value">
                {{ localData.proxy.config.path || "--" }}
              </div>
            </BkCol>
          </BkRow>
        </template>

        <template v-if="localData.proxy.type === 'mock'">
          <BkRow
            :class="{ 'ag-diff': checkDiff('localData.proxy.config.code') }"
          >
            <BkCol :span="4">
              <label class="ag-key">Status Code:</label>
            </BkCol>
            <BkCol :span="10">
              <div class="ag-value">
                {{ localData.proxy.config.code || "--" }}
              </div>
            </BkCol>
          </BkRow>

          <BkRow
            :class="{ 'ag-diff': checkDiff('localData.proxy.config.body') }"
          >
            <BkCol :span="4">
              <label class="ag-key">Response Body:</label>
            </BkCol>
            <BkCol :span="10">
              <div class="ag-value">
                <pre
                  v-if="localData.proxy.config.body"
                  class="ag-pre mt0"
                >{{
                    localData.proxy.config.body || "--"
                  }}</pre>
                <span v-else>--</span>
              </div>
            </BkCol>
          </BkRow>

          <BkRow
            :class="{ 'ag-diff': checkDiff('localData.proxy.config.headers') }"
          >
            <BkCol :span="4">
              <label class="ag-key">Headers:</label>
            </BkCol>
            <BkCol :span="10">
              <div v-if="isEmptyObject(localData.proxy.config.headers)">
                <ul class="ag-list">
                  <li
                    v-for="(headerItem, index) in localData.proxy.config
                      .headers"
                    :key="index"
                  >
                    {{ index }} : {{ headerItem }}
                  </li>
                </ul>
              </div>
              <span v-else>--</span>
            </BkCol>
          </BkRow>
        </template>
      </BkContainer>
    </template>
    <p
      class="title mt-15px"
      :class="{ 'ag-diff': checkDiff('localData.doc_updated_time') }"
    >
      {{ t("文档") }}
    </p>
    <BkContainer
      class="ag-kv-box"
      :col="14"
      :margin="6"
    >
      <BkRow :class="{ 'ag-diff': checkDiff('localData.doc_updated_time') }">
        <BkCol :span="4">
          <label class="ag-key">{{ t("文档更新时间") }}:</label>
        </BkCol>
        <BkCol :span="10">
          <div class="ag-value">
            <template v-if="localLanguage === 'en'">
              {{ localData.doc_updated_time.en || "--" }}
            </template>
            <template v-else>
              {{ localData.doc_updated_time.zh || "--" }}
            </template>
          </div>
        </BkCol>
      </BkRow>
    </BkContainer>

    <!--  插件  -->
    <div v-if="localData.plugins?.length">
      <template
        v-for="plugin in localData.plugins"
        :key="plugin.id"
      >
        <div
          class="container-diff"
          :class="getPluginDiffClass(plugin)"
        >
          <p class="title mt-15px">
            {{ t('插件:{name}', { name: plugin.name }) }}
          </p>
          <ConfigDisplayTable
            :plugin="plugin"
            first-col-width="auto"
          />
        </div>
      </template>
    </div>
  </div>
  <div v-else>
    --
  </div>
</template>

<script setup lang="ts">
import ConfigDisplayTable from '@/components/plugin-manage/ConfigDisplayTable.vue';
import Cookie from 'js-cookie';
import { useGateway } from '@/stores';

interface IProps {
  curResource?: any
  diffData?: any
  onlyShowDiff?: boolean
  backendsList?: any[]
  // 是否作为旧版本资源展示
  isSource?: boolean
}

const {
  curResource = null,
  diffData = {},
  onlyShowDiff = false,
  backendsList = [],
  isSource = false,
} = defineProps<IProps>();

const { t } = useI18n();
const gatewayStore = useGateway();

const diffMap = ref<any>({});
const localData = ref<any>({
  name: '',
  disabled_stages: [],
  config: {},
  proxy: {
    type: '',
    config: { transform_headers: { add: [] } },
  },
  useDefaultTimeout: true,
  useDefaultHeader: true,
  useDefaultHost: true,
  contexts: { resource_auth: { config: {} } },
});

const localLanguage = Cookie.get('blueking_language') || 'zh-cn';

const isEmptyObject = (data: any) => {
  if (data) {
    const keys = Object.keys(data);
    return !!keys.length;
  }
  return false;
};

const isString = (str: any) => {
  return typeof str === 'string';
};

const getResourceAuth = (auth: any) => {
  if (!auth) return '--';
  const tmpArr: string[] = [];

  if (auth?.auth_verified_required) {
    tmpArr.push(`${t('用户认证')}`);
  }
  if (auth?.app_verified_required) {
    tmpArr.push(`${t('蓝鲸应用认证')}`);
  }
  return tmpArr.join(', ');
};

const initLocalData = async () => {
  const data = JSON.parse(JSON.stringify(curResource));

  if (data.contexts.resource_auth.config) {
    if (isString(data.contexts.resource_auth.config)) {
      data.contexts.resource_auth.config = JSON.parse(data.contexts.resource_auth.config);
    }
  }
  else {
    data.config = {};
  }

  if (data.proxy.config) {
    if (isString(data.proxy.config)) {
      data.proxy.config = JSON.parse(data.proxy.config);
    }
  }
  else {
    data.proxy.config = {};
  }

  if (data.proxy.type === 'http') {
    data.useDefaultTimeout = !data.proxy.config.timeout;
    data.useDefaultHost = JSON.stringify(data.proxy.config.upstreams) === '{}';
    data.useDefaultHeader = JSON.stringify(data.proxy.config.transform_headers) === '{}';
  }
  localData.value = data;

  const backendId = localData.value?.proxy?.backend_id;
  if (backendId) {
    const curBackend: any = backendsList.find((item: any) => item.id === backendId);
    if (curBackend) {
      localData.value.proxy.backend_name = curBackend.name;
    }
  }
};

const initDiff = () => {
  diffMap.value = {};
  if (!diffData) {
    return false;
  }
  findAllDiff(diffData);

  // 处理后端配置使用默认配置情况
  if (diffMap.value['localData.proxy.config.timeout']) {
    diffMap.value['localData.useDefaultTimeout'] = true;
  }

  if (diffMap.value['localData.proxy.config.upstreams'] === '{}') {
    diffMap.value['localData.useDefaultHost'] = true;
  }

  if (diffMap.value['localData.proxy.config.transform_headers'] === '{}') {
    diffMap.value['localData.useDefaultHeader'] = true;
  }

  // 处理安全设置禁用环境
  const keys = Object.keys(diffMap.value);
  if (keys.some(item => item.startsWith('localData.disabled_stages'))) {
    diffMap.value['localData.disabled_stages'] = true;
  }
};

const findAllDiff = (value: any, prePath = 'localData') => {
  if (Array.isArray(value)) {
    if (value.length) {
      value.forEach((item) => {
        const path = `${prePath}`;
        findAllDiff(item, path);
      });
    }
    else {
      diffMap.value[prePath] = '[]';
    }
  }
  else if (typeof value === 'object') {
    if (JSON.stringify(value) === '{}') {
      diffMap.value[prePath] = '{}';
    }
    else {
      for (const key of Object.keys(value)) {
        const path = `${prePath}.${key}`;
        findAllDiff(value[key], path);
      }
    }
  }
  else {
    diffMap.value[prePath] = value;
  }
};

const checkDiff = (path: any) => {
  const keys = Object.keys(diffMap.value);
  return keys.some(item => item.startsWith(path));
};

const getPluginDiffClass = (plugin: any) => {
  // 检查传入的 plugin 是否记录在 diffMap 中
  const diffMapPluginKey = `localData.plugins.${plugin.code || plugin.type}`;
  const isPluginUpdated = Object.keys(diffMap.value).some(item => item.startsWith(diffMapPluginKey));

  // 插件在 diffMap 中，属于更新的内容，给予 item-updated 样式
  if (isPluginUpdated) {
    return 'item-updated';
  }

  // 插件不在 diffMap 中，检查传入的 plugin 是否存在于 curResource.diff.plugins 中
  // 如果存在，说明属于新增或删除的插件，如果不存在说明没有变动
  const diffPlugins = curResource?.diff?.plugins ?? {};
  const isPluginAddedOrDeleted = Object.keys(diffPlugins)
    .some((pluginCode: string) => pluginCode === (plugin.type || plugin.code));

  // 属于新增或删除的插件
  if (isPluginAddedOrDeleted) {
    // 传入了 isSource，表示当前 resource 作为旧数据展示，插件的变动属于被删除的内容，给予 item-deleted 样式
    if (isSource) {
      return 'item-deleted';
    }

    // 当前 resource 作为新数据展示，插件的变动属于新添加的内容，给予 item-deleted 样式
    return 'item-added';
  }

  // 插件没有变更，返回空 class，不改变样式
  return '';
};

// 网关标签
const labels = computed(() => gatewayStore.labels || []);

watch(
  () => curResource,
  () => {
    initDiff();
    initLocalData();
  },
);

initDiff();
initLocalData();
</script>

<style lang="scss" scoped>
.ag-dl {
  padding: 15px 40px 5px 30px;
}

.ag-diff {

  .ag-value {
    color: #fe9c00 !important;
  }

  .ag-pre {
    color: #fe9c00;
    background: #fbf4e9;
  }

  .ag-list {
    background: #fbf4e9;
  }
}

.ag-user-type {
  position: relative;
  width: 560px;
  height: 80px;
  padding: 17px 20px 0;
  overflow: hidden;
  background: #fafbfd;
  border: 1px solid #dcdee5;
  border-radius: 2px;

  .apigateway-icon {
    position: absolute;
    top: 15px;
    right: 20px;
    z-index: 0;
    font-size: 80px;
    color: #ecf2fc;
  }

  strong {
    display: block;
    margin-bottom: 10px;
    font-size: 13px;
    line-height: 1;
  }

  p {
    font-size: 12px;
    color: #63656e;
  }
}

.detail-wrapper {
  padding: 10px 20px 10px 10px;
  margin-top: 6px;
  background: #f0f1f5;
  border-radius: 2px;

  &.wrapper-diff {
    background: #fbf4e9;
  }

  .content-item {
    display: flex;
    font-size: 13px;
    line-height: 26px;
  }

  .key {
    display: inline-block;
    width: 100px;
    line-height: 28px;
    color: #63656e;
    text-align: right;
    vertical-align: middle;
  }

  .value {
    color: #313238;
    flex: 1;
  }
}

.ag-list {
  font-size: 13px;
  background: #fff;
  border: 1px solid #dcdee5;
  border-radius: 2px;

  > li {
    display: flex;
    padding: 5px 10px;
    line-height: 22px;
    background: #fff;

    .ds-key {
      white-space: nowrap;
    }

    .ds-value {
      padding-left: 5px;
      word-break: break-all;
      white-space: normal;
    }

    & + li {
      border-top: 1px solid #dcdee5;
    }
  }
}

.ag-tab-button {
  cursor: default;

  &:hover {
    color: #63656e;
    border-color: #c4c6cc;
  }

  &.is-selected {
    color: #3a84ff !important;
    border-color: #3a84ff !important;

    a {
      color: #3a84ff !important;
    }
  }
}

.ag-value {
  word-break: break-all;
  white-space: normal;
}

.bk-host-table {

  tr {
    background: #fff !important;
  }

  td,
  th {
    height: 36px;
    background: #fff !important;
  }
}

.container-diff {
  padding: 2px 8px;
  margin: 18px 0;

  &.item-added {
    background-color: rgb(45 203 86 / 10%);
  }

  &.item-updated {
    background-color: rgb(255 156 1 / 10%);
  }

  &.item-deleted {
    background-color: rgb(234 54 54 / 10%);
  }
}

.ag-kv-box {

  &.box-diff {
    padding-top: 10px;
    padding-bottom: 10px;
    background: #fbf4e9;
    border-radius: 2px;

    .ag-value,
    .ag-list {
      color: #fe9c00;
    }
  }

  .ag-key,
  .ag-value {
    font-size: 12px;
  }
}

.ag-resource-item {
  padding: 20px 30px;
  margin: 0 -30px;

  .title {
    padding-bottom: 10px;
    margin-bottom: 17px;
    font-size: 12px;
    font-weight: bold;
    color: #63656e;
    border-bottom: 1px solid #dcdee5;
  }

  &.show-diff {

    .title {
      display: none;

      &.ag-diff {
        display: block;
      }
    }

    .bk-grid-row {
      display: none;

      &.ag-diff {
        display: block;
      }
    }

    .box-diff {

      .bk-grid-row {
        display: block;
      }
    }
  }
}
</style>

<style lang="scss">
.bk-button-group .readonly-value {
  height: 32px;
  font-size: 13px;
  line-height: 32px;
  color: #313238;
}

.source-version {

  .detail-wrapper.wrapper-diff {
    background: #f0f1f5;
  }

  .ag-diff .ag-pre {
    color: #fff;
    background: #313238;
  }

  .ag-value,
  .ag-list {
    color: #313238 !important;
  }

  .ag-diff .ag-list {
    background: #fff;
  }

  .ag-diff .ag-value {
    color: #313238 !important;
  }

  .ag-kv-box.box-diff {
    background: #fff;
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
  }
}
</style>
