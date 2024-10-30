<template>
  <div class="ag-version-diff-box">
    <p class="summary-data">
      <strong class="ag-strong" style="color: #63656e">
        {{ $t("对比结果") }}：
      </strong>
      <template v-if="isDataLoading">
        <span>
          <spinner fill="#3a84ff" />
          {{ $t("正在努力对比中…") }}
        </span>
      </template>
      <template v-else-if="localSourceId || localTargetId">
        <span>
          {{ $t("新增") }}
          <strong class="ag-strong success m5">
            {{ diffData.add.length }}
          </strong>
          {{ $t("个资源") }}，
        </span>
        <span>
          {{ $t("更新") }}
          <strong class="ag-strong warning m5">
            {{ diffData.update.length }}
          </strong>
          {{ $t("个资源") }}，
        </span>
        <span>
          {{ $t("删除") }}
          <strong class="ag-strong danger m5">
            {{ diffData.delete.length }}
          </strong>
          {{ $t("个资源") }}
        </span>
      </template>
      <template v-else> -- </template>
    </p>

    <div class="search-data mb15">
      <bk-input
        clearable
        class="fl mr10"
        style="width: 310px"
        :placeholder="$t('请输入资源名称、资源地址或请求路径，回车结束')"
        type="search"
        v-model="searchParams.keyword"
        @enter="handleSearch"
        @clear="handleClear"
        @change="updateTableEmptyConfig()"
      >
      </bk-input>
      <bk-select
        class="fl mr10"
        v-model="searchParams.diffType"
        style="width: 140px"
        :clearable="true"
        :placeholder="$t('全部差异类型')"
        @change="updateTableEmptyConfig()"
      >
        <bk-option
          v-for="option in diffTypeList"
          :key="option.id"
          :id="option.id"
          :name="option.name"
        >
        </bk-option>
      </bk-select>
      <bk-checkbox
        class="fl"
        style="margin-top: 6px"
        :true-value="true"
        :false-value="false"
        v-model="searchParams.onlyUpdated"
      >
        {{ $t("仅显示有差异的资源属性") }}
      </bk-checkbox>

      <ul class="tag-list fr">
        <li><span class="tag success"></span> {{ $t("新增") }}</li>
        <li><span class="tag danger"></span> {{ $t("删除") }}</li>
        <li><span class="tag warning"></span> {{ $t("更新") }}</li>
      </ul>
    </div>

    <div :class="['diff-wrapper', { 'no-result': !hasResult }]">
      <div class="diff-header">
        <div class="source-header">
          <!-- <div class="marked">{{ $t("源版本") }}</div> -->
          <div class="version">
            <template v-if="localSourceId">
              <bk-select
                class="fl mr10 choose-version"
                v-model="localSourceId"
                v-if="sourceSwitch || pageType === 'createVersion'"
                :placeholder="$t('请选择源版本')"
                :clearable="false"
                :input-search="false"
                :filterable="true"
                @change="handleVersionChange">
                <template #trigger>
                  <span class="trigger-label" v-bk-tooltips="{ content: localSourceTriggerLabel, delay: 300 }">
                    {{ localSourceTriggerLabel }}
                  </span>
                  <DownShape class="trigger-label-icon" />
                </template>
                <bk-option
                  v-for="option in localVersionList"
                  :key="option.id"
                  :id="option.id"
                  :disabled="option.id === localTargetId"
                  :name="option.resource_version_display"
                >
                </bk-option>
              </bk-select>
              <strong class="title" v-else>
                <template v-if="pageType === 'publishEnvironment'">
                  {{ t('当前版本（{version}）', { version: sourceVersion.version }) }}
                </template>
                <template v-else>
                  {{ sourceVersion.version }} {{ sourceVersion.comment ? `(${sourceVersion.comment})` : '' }}
                </template>
              </strong>
            </template>
            <strong class="title" v-else>
              {{ t('暂无版本') }}
            </strong>
          </div>
        </div>
        <div class="target-header">
          <div class="version">
            <bk-select
              class="fl mr10 choose-version"
              v-model="localTargetId"
              v-if="targetSwitch && pageType !== 'createVersion'"
              :placeholder="$t('请选择目标版本')"
              :clearable="false"
              :input-search="false"
              :filterable="true"
              style="width: 320px"
              @change="handleVersionChange">
              <template #trigger>
                <span class="trigger-label">
                  {{ localTargetTriggerLabel }}
                  <DownShape class="trigger-label-icon" />
                </span>
              </template>
              <bk-option
                v-for="option in localVersionList"
                :key="option.id"
                :id="option.id"
                :disabled="option.id === localSourceId"
                :name="option.resource_version_display"
              >
              </bk-option>
            </bk-select>
            <strong class="title" v-else>
              <template v-if="pageType !== 'createVersion'">
                <template v-if="pageType === 'publishEnvironment'">
                  {{ t('待发布（{version}）', { version: targetVersion.version }) }}
                </template>
                <template v-else>
                  {{ targetVersion.version }} {{ targetVersion.comment ? `(${targetVersion.comment})` : '' }}
                </template>
              </template>
              <template v-else>
                {{t('当前最新资源列表')}}
              </template>
            </strong>
          </div>
          <!-- <div class="marked">{{ $t("目标版本") }}</div> -->
        </div>
        <button
          class="switch-btn"
          @click="handleSwitch"
          v-if="targetSwitch && sourceSwitch && localSourceId"
        >
          <i class="apigateway-icon icon-ag-exchange-line"></i>
        </button>
      </div>

      <div class="diff-main">
        <bk-loading :loading="isDataLoading" color="#ffffff" :opacity="1" :z-index="1000" class="diff-loading">
          <!-- 新增 -->
          <div class="diff-item" v-for="addItem in diffData.add" :key="addItem.id">
            <template v-if="checkMatch(addItem, 'add')">
              <div class="source-box">
                <div class="metadata pl10" @click="handleToggle(addItem)">
                  <!-- <i
                    :class="[
                      'bk-icon icon-right-shape',
                      { active: addItem.isExpanded },
                    ]"
                  ></i> -->
                  <RightShape class="expand-icon" v-if="!addItem.isExpanded" />
                  <DownShape class="expand-icon" v-else />
                  <span class="vm resource-title">--</span>
                </div>
                <div class="resource-box pl15 pr15">
                  <!-- <bk-transition :name="animation"> -->
                  <bk-exception
                    class="exception-part"
                    type="empty"
                    scene="part"
                    v-show="addItem.isExpanded"
                  >
                    {{ $t("此版本无该资源") }}
                  </bk-exception>
                  <!-- </bk-transition> -->
                </div>
              </div>
              <div class="target-box">
                <div class="metadata success" @click="handleToggle(addItem)">
                  <!-- <i :class="['bk-icon icon-right-shape', { active: addItem.isExpanded }]"></i> -->
                  <RightShape class="expand-icon" v-if="!addItem.isExpanded" />
                  <DownShape class="expand-icon" v-else />
                  <span
                    class="vm resource-title"
                    v-dompurify-html="renderTitle(addItem)"
                    :title="`【${addItem?.method}】${addItem?.path}`"
                  ></span>
                </div>
                <div class="resource-box pl15 pr15">
                  <!-- <bk-transition :name="animation"> -->
                  <resource-detail
                    :cur-resource="addItem"
                    :backends-list="backendsList"
                    v-show="addItem.isExpanded"
                  ></resource-detail>
                  <!-- </bk-transition> -->
                </div>
              </div>
            </template>
          </div>

          <!-- 删除 -->
          <div class="diff-item" v-for="deleteItem in diffData.delete" :key="deleteItem.id">
            <template v-if="checkMatch(deleteItem, 'delete')">
              <div class="source-box">
                <div class="metadata" @click="handleToggle(deleteItem)">
                  <!-- <i
                    :class="[
                      'bk-icon icon-right-shape',
                      { active: deleteItem.isExpanded },
                    ]"
                  ></i> -->
                  <RightShape class="expand-icon" v-if="!deleteItem.isExpanded" />
                  <DownShape class="expand-icon" v-else />
                  <span
                    class="vm resource-title"
                    v-dompurify-html="renderTitle(deleteItem)"
                    :title="`【${deleteItem?.method}】${deleteItem?.path}`"
                  ></span>
                </div>
                <div class="resource-box pl15 pr15">
                  <!-- <bk-transition :name="animation"> -->
                  <resource-detail
                    :cur-resource="deleteItem"
                    :backends-list="backendsList"
                    v-show="deleteItem.isExpanded"
                  ></resource-detail>
                  <!-- </bk-transition> -->
                </div>
              </div>
              <div class="target-box">
                <div class="metadata danger" @click="handleToggle(deleteItem)">
                  <!-- <i
                    :class="[
                      'bk-icon icon-right-shape',
                      { active: deleteItem.isExpanded },
                    ]"
                  ></i> -->
                  <RightShape class="expand-icon" v-if="!deleteItem.isExpanded" />
                  <DownShape class="expand-icon" v-else />
                  <span
                    class="vm resource-title"
                    v-dompurify-html="renderTitle(deleteItem)"
                    :title="`【${deleteItem?.method}】${deleteItem?.path}`"
                  ></span>
                </div>
                <div class="resource-box pl15 pr15">
                  <!-- <bk-transition :name="animation"> -->
                  <resource-detail
                    style="opacity: 0.35"
                    :cur-resource="deleteItem"
                    :backends-list="backendsList"
                    v-show="deleteItem.isExpanded"
                  >
                  </resource-detail>
                  <!-- </bk-transition> -->
                </div>
              </div>
            </template>
          </div>

          <!-- 更新 -->
          <div
            class="diff-item"
            v-for="updateItem in diffData.update" :key="`${updateItem.source.id}:${updateItem.target.id}`">
            <template v-if=" checkMatch(updateItem.source, 'update') || checkMatch(updateItem.target, 'update')">
              <div class="source-box">
                <div class="metadata" @click="handleToggle(updateItem)">
                  <!-- <i
                    :class="[
                      'bk-icon icon-right-shape',
                      { active: updateItem.isExpanded },
                    ]"
                  ></i> -->
                  <RightShape class="expand-icon" v-if="!updateItem.isExpanded" />
                  <DownShape class="expand-icon" v-else />
                  <span
                    class="vm resource-title"
                    v-dompurify-html="renderTitle(updateItem.source)"
                    :title="`【${updateItem?.source?.method}】${updateItem?.source?.path}`"
                  ></span>
                </div>
                <div class="resource-box pl15 pr15">
                  <!-- <bk-transition :name="animation"> -->
                  <resource-detail
                    class="source-version"
                    :cur-resource="updateItem.source"
                    :backends-list="backendsList"
                    v-show="updateItem.isExpanded"
                    :diff-data="updateItem.target.diff"
                    :only-show-diff="searchParams.onlyUpdated"
                    is-source
                  ></resource-detail>
                  <!-- </bk-transition> -->
                </div>
              </div>
              <div class="target-box">
                <div class="metadata warning" @click="handleToggle(updateItem)">
                  <!-- <i
                    :class="[
                      'bk-icon icon-right-shape',
                      { active: updateItem.isExpanded },
                    ]"
                  ></i> -->
                  <RightShape class="expand-icon" v-if="!updateItem.isExpanded" />
                  <DownShape class="expand-icon" v-else />
                  <span
                    class="vm resource-title"
                    v-dompurify-html="renderTitle(updateItem.target)"
                    :title="`【${updateItem?.target?.method}】${updateItem?.target?.path}`"
                  ></span>
                </div>
                <!-- {{updateItem.source.diff}} -->

                <div class="resource-box pl15 pr15">
                  <!-- <bk-transition :name="animation"> -->
                  <resource-detail
                    :cur-resource="updateItem.target"
                    :backends-list="backendsList"
                    v-show="updateItem.isExpanded"
                    :diff-data="updateItem.source.diff"
                    :only-show-diff="searchParams.onlyUpdated"
                  ></resource-detail>
                  <!-- </bk-transition> -->
                </div>
              </div>
            </template>
          </div>

          <template v-if="!hasResult && !isDataLoading">
            <!-- 无数据 -->
            <TableEmpty
              v-if="hasFilter"
              :keyword="tableEmptyConf.keyword"
              :abnormal="tableEmptyConf.isAbnormal"
              @reacquire="getDiffData"
              @clear-filter="handleClearFilterKey"
            />
            <bk-exception
              class="mt50 diff-tips"
              type="search-empty"
              scene="part"
              v-else
            >
              {{
                !localTargetId
                  ? $t("请选择目标版本")
                  : $t("版本资源配置无差异")
              }}
            </bk-exception>
          </template>
        </bk-loading>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import resourceDetail from '@/components/resource-detail/index.vue';
import { useI18n } from 'vue-i18n';
import { Spinner, RightShape, DownShape } from 'bkui-vue/lib/icon';
import { useCommon } from '@/store';
import TableEmpty from '@/components/table-empty.vue';
import { resourceVersionsDiff, getResourceVersionsList, getGatewayLabels, getBackendsListData } from '@/http';

const { t } = useI18n();
const route = useRoute();
const common = useCommon();

// 网关id
const apigwId = computed(() => +route.params.id);
const tableEmptyConf = ref<{ keyword: string; isAbnormal: boolean }>({
  keyword: '',
  isAbnormal: false,
});

const props = defineProps({
  versionList: {
    type: Array,
    default: () => [],
  },
  sourceId: {
    type: [Number, String],
    default: '',
  },
  targetId: {
    type: [Number, String],
    default: '',
  },
  sourceSwitch: {
    type: Boolean,
    default: true,
  },
  targetSwitch: {
    type: Boolean,
    default: true,
  },
  curDiffEnabled: {
    type: Boolean,
    default: true,
  },
  pageType: {
    type: String, // createVersion: 生成资源版本  publishEnvironment: 发布到环境
    default: '',
  },
});

const width = ref<number>(1240);
const isDataLoading = ref<boolean>(false);
const localSourceId = ref(props.sourceId);
const localTargetId = ref(props.targetId || 'current');
const localVersionList = ref<any[]>(props.versionList);
const diffData = reactive<any>({
  add: [],
  delete: [],
  update: [],
});
// const animation = ref('collapse');
const searchKeyword = ref('');
const searchParams = reactive({
  keyword: '',
  diffType: '',
  onlyUpdated: false,
});
const diffTypeList = reactive([
  {
    id: 'add',
    name: t('新增'),
  },
  {
    id: 'delete',
    name: t('删除'),
  },
  {
    id: 'update',
    name: t('更新'),
  },
]);

const hasResult = computed(() => {
  const addItem = diffData.add.some((item: any) => {
    return checkMatch(item, 'add');
  });

  const deleteItem = diffData.delete.some((item: any) => {
    return checkMatch(item, 'delete');
  });

  const updateItem = diffData.update.some((item: any) => {
    return (
      checkMatch(item.source, 'update') || checkMatch(item.target, 'update')
    );
  });

  return addItem || deleteItem || updateItem || isDataLoading.value;
});

const hasFilter = computed(() => searchKeyword.value || searchParams.diffType);

const sourceVersion = computed(() => {
  const match = localVersionList.value.find(item => item.id === localSourceId.value);
  if (match) {
    return match;
  }
  return {
    id: '',
    comment: '',
    version: '',
  };
});

const targetVersion = computed(() => {
  const match = localVersionList.value.find(item => item.id === localTargetId.value);
  if (match) {
    return match;
  }
  return {
    id: '',
    comment: '',
    version: '',
  };
});

const handleToggle = (item: any) => {
  item.isExpanded = !item.isExpanded;
};

const handleSearch = (keyword?: string) => {
  searchKeyword.value = keyword || '';
};

const handleClear = () => {
  searchKeyword.value = '';
};

const handleSwitch = async () => {
  [localSourceId.value, localTargetId.value] = [
    localTargetId.value,
    localSourceId.value,
  ];
  await getDiffData();
};

const checkMatch = (item: any, type: any) => {
  if (searchParams.diffType && searchParams.diffType !== type) {
    return false;
  }
  const method = item?.method?.toLowerCase();
  const path = item?.path?.toLowerCase();
  const backendPath = item?.proxy?.config?.path?.toLowerCase();
  const name = item?.name?.toLowerCase();
  const keyword = searchKeyword.value.toLowerCase();
  return (
    method.indexOf(keyword) > -1
    || path.indexOf(keyword) > -1
    || backendPath.indexOf(keyword) > -1
    || name.indexOf(keyword) > -1
  );
};

const renderTitle = (item: any) => {
  let { method, path } = item;
  if (searchKeyword.value) {
    const reg = new RegExp(`(${searchKeyword.value})`, 'ig');
    method = method.replace(reg, '<i class="keyword ag-strong primary">$1</i>');
    path = path.replace(reg, '<i class="keyword ag-strong primary">$1</i>');
  }

  // return `【${method}】${path}`;

  // POST = 'info', GET = 'success', DELETE = 'danger', PUT = 'warning', PATCH = 'info', ANY = 'success',
  let tagCls = 'bk-tag-info';
  switch (method) {
    case 'POST':
      tagCls = 'bk-tag-info';
      break;
    case 'GET':
      tagCls = 'bk-tag-success';
      break;
    case 'DELETE':
      tagCls = 'bk-tag-danger';
      break;
    case 'PUT':
      tagCls = 'bk-tag-warning';
      break;
    case 'PATCH':
      tagCls = 'bk-tag-info';
      break;
    case 'ANY':
      tagCls = 'bk-tag-success';
      break;
    default:
      break;
  }
  return `<div class="bk-tag ${tagCls} bk-tag--default" style="border-radius: 2px;margin-right: 4px;">`
      + `<span class="bk-tag-text">${method}</span>`
      + `</div><span class="title-content">${path}</span>`;
};

const updateTableEmptyConfig = () => {
  const isSearch = !!searchParams.keyword || !!searchParams.diffType;
  if (isSearch && !hasResult.value) {
    tableEmptyConf.value.keyword = 'placeholder';
    return;
  }
  if (isSearch) {
    tableEmptyConf.value.keyword = '$CONSTANT';
    return;
  }
  tableEmptyConf.value.keyword = '';
};

const handleClearFilterKey = async () => {
  searchParams.keyword = '';
  searchParams.diffType = '';
  searchKeyword.value = '';
  await getDiffData();
  updateTableEmptyConfig();
};

const handleVersionChange = async () => {
  searchParams.keyword = '';
  searchParams.diffType = '';
  searchParams.onlyUpdated = false;
  searchKeyword.value = '';
  await getDiffData();
};

const getDiffData = async () => {
  // localSourceId 可以为 0
  if (isDataLoading.value || localSourceId.value === '') {
    return false;
  }

  isDataLoading.value = true;

  diffData.add = [];
  diffData.delete = [];
  diffData.update = [];

  try {
    const res = await resourceVersionsDiff(apigwId.value, {
      source_resource_version_id: String(localSourceId.value).replace(
        'current',
        '',
      ),
      target_resource_version_id: String(localTargetId.value).replace(
        'current',
        '',
      ),
    });

    res.add.forEach((item: any) => {
      item.isExpanded = false;
    });
    res.delete.forEach((item: any) => {
      item.isExpanded = false;
    });
    res.update.forEach((item: any) => {
      item.isExpanded = false;

      if (item?.source?.diff?.proxy?.backend_id) {
        const curBackend: any = backendsList.value?.find((backend: any) => {
          return backend.id === item.source.diff.proxy.backend_id;
        });
        item.source.diff.proxy.backend_name = curBackend?.name || '';
      }

      if (item?.target?.diff?.proxy?.backend_id) {
        const curBackend: any = backendsList.value?.find((backend: any) => {
          return backend.id === item.target.diff.proxy.backend_id;
        });
        item.target.diff.proxy.backend_name = curBackend?.name || '';
      }
    });

    diffData.add = res.add;
    diffData.delete = res.delete;
    diffData.update = res.update;
  } catch (e) {
    console.log(e);
  } finally {
    setTimeout(() => {
      isDataLoading.value = false;
    }, 1000);
  }
};

const getApigwVersions = async () => {
  const pageParams = {
    limit: 999,
    offset: 0,
  };
  try {
    const res = await getResourceVersionsList(apigwId.value, pageParams);
    res.results.forEach((item: any) => {
      item.resource_version_display = item.comment ? `${item.version}(${item.comment})` : item.version;
      item.stage_text = item.released_stages.map((item: any) => {
        return item.name;
      });
    });

    if (props.curDiffEnabled) {
      localVersionList.value = [
        {
          id: 'current',
          name: t('当前最新资源列表'),
          resource_version_display: t('当前最新资源列表'),
        },
        ...res.results,
      ];
    } else {
      localVersionList.value = res.results;
    }
  } catch (e) {
    console.log(e);
  }
};

const getLabels = async () => {
  try {
    const res = await getGatewayLabels(apigwId.value);
    common.setGatewayLabels(res);
  } catch (e) {
    console.log(e);
  }
};

const backendsList = ref([]);
// 后端服务列表
const getBackendsList = async () => {
  try {
    const res = await getBackendsListData(apigwId.value);
    backendsList.value = res.results || [];
  } catch (e) {
    console.log(e);
  }
};

const init = async () => {
  await Promise.all([
    getDiffData(),
    getApigwVersions(),
    getLabels(),
    getBackendsList(),
  ]);
};

const localSourceTriggerLabel = computed(() => {
  const match = localVersionList.value.find((item: any) => item.id === localSourceId.value);
  if (match) {
    return match.resource_version_display;
  }
  return '';
});

const localTargetTriggerLabel = computed(() => {
  const match = localVersionList.value.find((item: any) => item.id === localTargetId.value);
  if (match) {
    return match.resource_version_display;
  }
  return '';
});

watch(
  () => [props.sourceId, props.targetId],
  async (newArr) => {
    const [sourceId, targetId] = newArr;
    localSourceId.value = sourceId;
    localTargetId.value = targetId || 'current';
    isDataLoading.value = false;
    await getDiffData();
  },
);

width.value = window.innerWidth <= 1280 ? 1000 : 1240;

onMounted(() => {
  init();
});
</script>

<style lang="scss" scoped>
.summary-data {
  margin-bottom: 15px;
  font-size: 14px;
  color: #63656e;
  background-color: #f5f7fa;
  height: 40px;
  line-height: 40px;
  padding: 0 16px;
}

.search-data {
  &::after {
    content: "";
    display: table;
    clear: both;
  }
}

.tag-list {
  height: 32px;
  line-height: 32px;

  li {
    display: inline-block;
    margin-left: 10px;
    font-size: 13px;
    color: #63656e;

    .tag {
      width: 10px;
      height: 10px;
      display: inline-block;
      margin-right: 5px;

      &.success {
        background: #dcffe2;
        border: 1px solid #94f5a4;
      }

      &.danger {
        background: #ffe9e8;
        border: 1px solid #ffbdbd;
      }

      &.warning {
        background: #ffefd6;
        border: 1px solid #ffe3b5;
      }
    }
  }
}

.diff-wrapper {
  border: 1px solid #dcdee5;
  border-radius: 2px;
  min-height: 300px;
  position: relative;

  &.no-result {
    &::after {
      display: none;
    }
  }

  &::after {
    content: "";
    display: inline-block;
    position: absolute;
    width: 1px;
    background: #dbdee4;
    left: 50%;
    top: 0;
    height: 100%;
    z-index: 100;
    margin-left: -1px;
  }
}

.diff-main {
  max-height: calc(100vh - 362px);
  min-height: 300px;
  overflow-y: auto;
  overflow-x: hidden;
  .diff-loading {
    min-height: 300px;
    padding: 6px 0px;
  }
}

.diff-item {
  .source-box,
  .target-box {
    padding: 6px 12px;

    .metadata {
      height: 36px;
      line-height: 36px;
      border-radius: 2px;
      background: #f0f1f5;
      // border: 1px solid #f0f1f5;
      font-size: 12px;
      font-weight: bold;
      color: #63656e;
      padding-left: 10px;
      cursor: pointer;
      position: relative;

      .expand-icon {
        position: absolute;
        top: 12px;
        z-index: 1;
        color: #979ba5;
      }

      .resource-title {
        position: relative;
        max-width: 550px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        display: inline-block;
        width: 96%;
        font-weight: 700;
        margin-left: 18px;
        :deep(.bk-tag-text) {
          font-weight: 400;
        }
      }

      // .bk-icon {
      //   display: inline-block;
      //   transform-origin: center;
      //   transition: all ease 0.3s;

      //   &.active {
      //     transform: rotate(90deg);
      //   }
      // }

      &.danger {
        background: #fef2f2;
        // border-color: #fe9c9c;

        .resource-title {
          color: #ea3636;
          :deep(.title-content) {
            text-decoration: line-through;
          }
        }
      }

      &.success {
        background: #f0fcf4;
        // border-color: #94f5a4;
        .resource-title {
          color: #2dcb56;
        }
      }

      &.warning {
        background: #fff9ef;
        // border-color: #ffd694;
        .resource-title {
          color: #ff9c01;
        }
      }
    }
  }

  // .source-box {
  //   border-right: 1px solid #dcdee5;
  // }

  // .target-box {
  //   border-left: 1px solid #dcdee5;
  // }

  .resource-box {
    height: calc(100% - 36px);
    position: relative;

    .exception-part {
      position: absolute;
      left: 0;
      top: calc(50% - 40px);
      transform: translateY(-50%);
    }
  }

  .delete-icon {
    width: 68px;
    height: 68px;
    position: absolute;
    right: 20px;
    top: 20px;
    z-index: 10;
  }
}

.diff-header {
  display: flex;
  position: relative;

  .switch-btn {
    position: absolute;
    left: 50%;
    top: 50%;
    width: 27px;
    height: 27px;
    background: #fff;
    box-shadow: 0px 2px 4px 0px rgba(0, 0, 0, 0.1);
    transform: translateY(-50%) translateX(-50%);
    border: none;
    border-radius: 50%;
    color: #63656e;
    z-index: 110;

    &:hover {
      color: #3a84ff;
    }

    i {
      margin-top: -4px;
      display: inline-block;
      vertical-align: middle;
    }
  }

  .source-header,
  .target-header {
    width: 50%;
    height: 42px;
    background-color: #f0f1f5;
    line-height: 42px;
    display: flex;

    .choose-version {
      width: 320px;
      cursor: pointer;
      :deep(.bk-select-trigger) {
        display: flex;
        align-items: center;
        justify-content: center;
      }
      .trigger-label {
        position: relative;
        display: inline-block;
        max-width: 180px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin-right: 4px;
      }
      // .trigger-label-icon {
      //   position: absolute;
      //   top: 15px;
      //   right: 0;
      // }
    }

    .marked {
      width: 130px;
      text-align: center;
      font-size: 13px;
      color: #63656e;
    }

    .version {
      flex: 1;
      text-align: center;
      position: relative;
    }

    .title {
      flex: 1;
      font-size: 13px;
      color: #63656e;
      text-align: center;
      font-weight: 700;
    }
  }

  .source-header {
    border-right: 1px solid #dcdee5;
    border-bottom: 1px solid #dcdee5;
    background-color: #f5f7fa;

    .marked {
      border-right: 1px solid #dcdee5;
    }
  }

  .target-header {
    background-color: #f0f1f5;
    // border-left: 1px solid #dcdee5;
    border-bottom: 1px solid #dcdee5;

    .marked {
      border-left: 1px solid #dcdee5;
    }
  }
}
.diff-item {
  display: flex;

  .source-box,
  .target-box {
    width: 50%;
  }
}
</style>

<style lang="scss">
.version {
  .bk-select {
    border: none;
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    font-size: 13px;
    font-weight: 700;
    color: #63656e;
    &.is-default-trigger.is-unselected:before {
      width: 280px;
      font-weight: 700;
      color: #63656e;
      font-size: 13px;
      text-align: center;
    }
    .bk-input {
      border: none;
    }
    .bk-input--text {
      background: transparent;
    }
    .bk-input--text::placeholder {
      font-size: 13px;
      font-weight: 700;
      color: #63656e;
      text-align: center;
    }
    &.is-focus .bk-input--default {
      box-shadow: none;
    }
  }
}
.diff-tips {
  color: #63656E;
}
</style>
