<template>
  <div>
    <BkButton
      class="mr-10px"
      @click="handleBatchRemovePolicy"
    >
      {{ t('批量删除') }}
    </BkButton>
    <BkButton
      class="mr-10px"
      @click="handleAddResource"
    >
      {{ t('添加') }}
    </BkButton>
    <!-- 按蓝鲸应用ID 资源名称搜索 -->
    <BkSearchSelect
      v-model="searchFilters"
      class="float-right w-500px"
      :placeholder="t('搜索')"
      show-popover-tag-change
      clearable
      :data="searchResourceCondition"
      :show-condition="false"
      @change="formatFilterData"
      @clear="clearSearchFilters"
    />

    <BkLoading :loading="isTableLoading">
      <BkTable
        :data="pagingList"
        remote-pagination
        :size="'small'"
        :max-height="600"
        :pagination="pagination"
        style="margin-top: 15px;"
        border="outer"
        @header-dragend="dragendColumn"
        @row-click="tableRowClick"
        @page-value-change="handlePageChange"
        @page-limit-change="handlePageLimitChange"
        @select-all="handleSelectAll"
        @selection-change="handleResourceSelect"
      >
        <BkTableColumn
          align="center"
          width="40"
        >
          <template #default="{ row }">
            <div
              v-if="row.dimension !== 'api'"
              class="play-shape"
              :class="[row.isIconView ? 'icon-view' : 'icon-conceal']"
            >
              <i class="bk-icon icon-play-shape" />
            </div>
          </template>
        </BkTableColumn>
        <BkTableColumn
          type="selection"
          width="60"
          align="center"
        />
        <BkTableColumn
          :label="t('蓝鲸应用ID')"
          prop="bk_app_code"
        />
        <BkTableColumn
          :label="t('类型')"
          prop="dimension"
        >
          <template #default="{ row }">
            <template v-if="row.dimension === 'api'">
              {{ t('全部资源') }}
            </template>
            <template v-if="row.dimension === 'resource'">
              {{ t('具体资源') }}
            </template>
          </template>
        </BkTableColumn>
        <BkTableColumn
          :label="t('资源')"
          prop="resource_ids"
          :show-overflow-tooltip="false"
        >
          <template #default="{ row }">
            <template v-if="row.dimension === 'api'">
              *
            </template>
            <template v-else>
              <template v-if="row.resource_ids && row.resource_ids.length && !row.isIconView">
                <BkPopover
                  placement="top"
                  :ext-cls="'aaaaaa'"
                >
                  <div
                    class="parent"
                    :style="{ 'height': row.rowHeight }"
                  >
                    <!-- 设置宽度 -->
                    <div
                      class="column-wrapper"
                      :style="{ width: eleTargetWidth + 'px' }"
                    >
                      <span
                        v-for="(item, index) in formattedData(row.resource_ids)"
                        :key="item.id"
                      >
                        {{ item.name }}<span v-if="!(index === row.resource_ids.length - 1)">,</span>
                      </span>
                    </div>
                  </div>
                  <template #content>
                    <div style="white-space: normal;">
                      <p
                        v-for="item in formattedData(row.resource_ids)"
                        :key="item.id"
                      >
                        {{ item.name }}
                      </p>
                    </div>
                  </template>
                </BkPopover>
              </template>
              <template v-else-if="row.isIconView">
                <div
                  class="parent"
                  :style="{ 'height': row.rowHeight }"
                >
                  <div>
                    <span
                      v-for="item in formattedData(row.resource_ids)"
                      :key="item.id"
                      class="text-view"
                    >
                      {{ item.name }}
                    </span>
                  </div>
                </div>
              </template>
              <template v-else>
                --
              </template>
            </template>
          </template>
        </BkTableColumn>
        <BkTableColumn
          :label="t('操作')"
          :show-overflow-tooltip="false"
          width="120"
        >
          <template #default="{ row }">
            <BkButton
              class="mr-10px"
              text
              theme="primary"
              @click.stop="handleEditResource(row)"
            >
              {{ t('编辑') }}
            </BkButton>
            <BkPopConfirm
              placement="top"
              :content="t('确认删除？')"
              @confirm="handlerDeletePolicy(row)"
            >
              <BkButton
                class="mr-10px"
                text
                theme="primary"
              >
                {{ t('删除') }}
              </BkButton>
            </BkPopConfirm>
          </template>
        </BkTableColumn>
        <template #empty>
          <TableEmpty
            :keyword="tableEmptyConf.keyword"
            :abnormal="tableEmptyConf.isAbnormal"
            @reacquire="getTableData"
            @clear-filter="handleClearFilterKey"
          />
        </template>
      </BkTable>
    </BkLoading>

    <BkSideslider
      v-model:is-show="resourceSliderConf.isShow"
      :title="resourceSliderConf.title"
      :width="800"
      quick-close
      :before-close="handleBeforeClose"
      @hidden="sidesliderHidden"
    >
      <template #default>
        <div class="p30">
          <BkForm
            ref="validateForm1"
            :label-width="30"
            :model="curResource"
            :rules="rules"
          >
            <BkFormItem label="">
              <p class="top-tips">
                {{ t('你将对指定的蓝鲸应用添加免用户认证白名单') }}
              </p>
            </BkFormItem>
            <BkFormItem
              :label="t('蓝鲸应用ID')"
              required
              :label-width="150"
              :property="'bkAppCode'"
              :rules="rules.bkAppCode"
              :error-display-type="'normal'"
            >
              <BkInput
                v-model="curResource.bkAppCode"
                :placeholder="t('请输入应用ID')"
                :disabled="resourceSliderConf.type === 'edit'"
              />
            </BkFormItem>
            <BkFormItem label="">
              <p class="top-tips">
                {{ t('请选择要添加的资源') }}
              </p>
            </BkFormItem>
            <BkFormItem
              label=""
              :label-width="56"
            >
              <BkRadioGroup
                v-model="manner"
                style="display: block;"
              >
                <BkRadio label="api">
                  {{ t('全部资源') }}
                  <i
                    v-bk-tooltips.right="t('包括网关下所有资源，包括未来新创建的资源')"
                    class="apigateway-icon icon-ag-info icon-class"
                  />
                </BkRadio>
                <br>
                <BkRadio
                  label="resource"
                  style="margin-left: 0;"
                >
                  {{ t('具体资源') }}
                  <i
                    v-bk-tooltips.right="t('仅包含当前选择的资源')"
                    class="apigateway-icon icon-ag-info icon-class"
                  />
                </BkRadio>
              </BkRadioGroup>
            </BkFormItem>
            <BkFormItem
              v-if="manner === 'resource'"
              label=""
            >
              <div class="white-transfer-wrapper">
                <BkTransfer
                  ext-cls="resource-transfer-wrapper"
                  :target-list="resourceTargetList"
                  :source-list="resourceList"
                  :display-key="'name'"
                  :setting-key="'id'"
                  :title="[t('未选资源'), t('已选资源')]"
                  searchable
                  @change="handleResourceChange"
                >
                  <template #source-option="data">
                    <div
                      class="transfer-source-item"
                      :title="data.name"
                    >
                      {{ data.name }}
                    </div>
                  </template>
                  <template #target-option="data">
                    <div
                      class="transfer-source-item"
                      :title="data.name"
                    >
                      {{ data.name }}
                    </div>
                  </template>
                </BkTransfer>
                <p class="tips-text">
                  <AgIcon
                    name="info"
                    class="icon-class"
                  />
                  {{ t('仅展示需要认证用户的资源') }}
                </p>
              </div>
            </BkFormItem>
            <BkFormItem label="">
              <BkButton
                theme="primary"
                class="mr-10px"
                :disabled="confirmLoading"
                @click="handleBindResource"
              >
                {{ t('确定') }}
              </BkButton>
              <BkButton @click="handleHideResourceSlider">
                {{ t('取消') }}
              </BkButton>
            </BkFormItem>
          </BkForm>
        </div>
      </template>
    </BkSideslider>
  </div>
</template>

<script lang="ts" setup>
import { json2Yaml, yaml2Json } from '@/utils';
import { throttle } from 'lodash-es';
import { InfoBox, Message } from 'bkui-vue';
import TableEmpty from '@/components/table-empty/index.vue';
import { useRouteParams } from '@vueuse/router';
import { getVerifiedUserRequiredResources } from '@/services/source/resource.ts';

interface IProps {
  yamlStr?: string
  type?: string
}

const {
  yamlStr = '',
  type = 'create',
} = defineProps<IProps>();

const { t } = useI18n();

const gatewayId = useRouteParams('id', 0, { transform: Number });
const validateForm1 = ref();
const keyword = ref('');
const dataList = ref<any>([]);
const pagingList = ref<any>([]);
const searchList = ref<any>([]);
const pagination = reactive({
  current: 1,
  count: 0,
  limit: 10,
});
const whiteListPolicyList = ref<any>([]);
const resourceSliderConf = reactive({
  isShow: false,
  type: 'add',
  title: t('添加白名单'),
});
const resourceTargetList = ref<any>([]);
const resourceList = ref<any>([]);
const resourceIds = ref<any>([]);
const manner = ref('api');
const curResource = reactive({ bkAppCode: '' });
const isTableLoading = ref(false);
const confirmLoading = ref(false);
const searchResourceCondition = reactive<any>([
  {
    name: t('蓝鲸应用ID'),
    id: 'bk_app_code',
    children: [],
  },
  {
    name: t('资源名称'),
    id: 'resource_id',
    children: [],
  },
]);
const searchFilters = ref<any>([]);
const searchParams = ref<any>({
  bk_app_code: '',
  resource_id: '',
});
const eleTargetWidth = ref<string | number>('150');
const rules = reactive<any>({
  bkAppCode: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
    {
      regex: /^[a-z0-9][a-z0-9_-]{0,31}$/,
      message: t('由小写字母、数字、连字符(-)组成，首字符必须是字母，长度小于 32 个字符'),
      trigger: 'blur',
    },
  ],
});
const tableEmptyConf = ref<{
  keyword: string
  isAbnormal: boolean
}>({
  keyword: '',
  isAbnormal: false,
});
const sourceEl = ref<any>(null);

const formattedData = computed(() => {
  return (resourceIds: any) => {
    const list = resourceList.value.filter((item: any) => {
      return !!resourceIds.includes(item.id);
    });
    return list.length ? list : '--';
  };
});

watch(
  () => keyword.value,
  (value) => {
    if (value === '') {
      getTableData();
    }
  },
);

watch(
  () => searchFilters.value,
  () => {
    nextTick(() => {
      searchParams.value.bk_app_code = '';
      searchParams.value.resource_id = '';
      searchFilters.value.forEach((item: any) => {
        searchParams.value[item.id] = item.values[0].id;
      });
    });
  },
);

watch(
  () => searchParams.value.bk_app_code,
  () => {
    pagination.current = 1;
    pagination.count = 0;
    getSearchDataList();
  },
);

watch(
  () => searchParams.value.resource_id,
  () => {
    pagination.current = 1;
    pagination.count = 0;
    getSearchDataList();
  },
);

const handleBeforeClose = async () => {
  // 添加
  const initData: any = {
    ...curResource,
    manner: manner.value,
  };
  // 编辑
  if (resourceSliderConf.type === 'edit') {
    initData.resourceIds = resourceIds.value;
  }

  // isSidebarClosed(JSON.stringify(initData)).then((close) => {
  //   resourceSliderConf.isShow = !close;
  // });
};

const removeResourceScroll = () => {
  sourceEl.value?.forEach((el: any) => {
    el.removeEventListener('scroll', hideToolTips);
  });
};

const hideToolTips = throttle(() => {
  const tipsEl = document.querySelectorAll('.tippy-popper');
  if (tipsEl.length) {
    tipsEl[0].parentNode.removeChild(tipsEl[tipsEl.length - 1]);
  }
}, 60);

const handleResourceScroll = async () => {
  nextTick(() => {
    sourceEl.value = document.querySelectorAll('.white-transfer-wrapper ul.content');
    sourceEl.value.forEach((el: any) => {
      el.addEventListener('scroll', hideToolTips);
    });
  });
};

const updateTableEmptyConfig = () => {
  tableEmptyConf.value.isAbnormal = pagination.abnormal;
  if (searchFilters.value?.length || !pagingList.value.length) {
    tableEmptyConf.value.keyword = 'placeholder';
    return;
  }
  if (searchFilters.value?.length) {
    tableEmptyConf.value.keyword = '$CONSTANT';
    return;
  }
  tableEmptyConf.value.keyword = '';
};

const handleClearFilterKey = () => {
  searchFilters.value = [];
  getTableData();
  updateTableEmptyConfig();
};

const getResourcesViewWidth = () => {
  nextTick(() => {
    setTimeout(() => {
      let content: any = document.querySelector('.parent');
      if (content) {
        while (content.tagName !== 'BODY') {
          content = content.parentNode;
          if (content.className === 'cell') {
            eleTargetWidth.value = content.clientWidth - 20;
            break;
          }
        }
      }
    }, 0);
  });
};

const dragendColumn = (newWidth?: any) => {
  eleTargetWidth.value = newWidth - 20;
};

const tableRowClick = (_: any, row: any) => {
  handlerIcon(row);
};

const clearSearchFilters = () => {
  getTableData();
};

const filterSearchList = (key: any) => {
  isTableLoading.value = true;
  if (key === 'all') {
    pagingList.value = dataList.value.filter((item: any) => {
      if (item.bk_app_code === searchParams.value.bk_app_code
        && item.resource_ids.includes(searchParams.value.resource_id)) {
        return true;
      }
      return false;
    });
  }
  else {
    if (key === 'bk_app_code') {
      pagingList.value = dataList.value.filter((item: any) => {
        if (item.bk_app_code === searchParams.value[key]) {
          return true;
        }
        return false;
      });
    }
    else {
      pagingList.value = dataList.value.filter((item: any) => {
        if (item.resource_ids.includes(searchParams.value[key])) {
          return true;
        }
        return false;
      });
    }
  }
  searchList.value = pagingList.value;
  pagination.count = pagingList.value.length || 0;
  setTimeout(() => {
    isTableLoading.value = false;
  }, 300);
};

const getSearchDataList = () => {
  if (!searchParams.value.bk_app_code && !searchParams.value.resource_id) {
    getTableData();
    return;
  }
  if (searchParams.value.bk_app_code && searchParams.value.resource_id) {
    filterSearchList('all');
  }
  else {
    if (searchParams.value.bk_app_code) {
      filterSearchList('bk_app_code');
    }
    if (searchParams.value.resource_id) {
      filterSearchList('resource_id');
    }
  }
  updateTableEmptyConfig();
};

const formatFilterData = () => {
  const map: any = {};
  searchFilters.value.forEach((filter: any) => {
    map[filter.id] = filter;
  });
  const keys = Object.keys(map);
  searchFilters.value = [];
  keys.forEach((key) => {
    searchFilters.value.push(map[key]);
  });
};

const handlerIcon = (data: any) => {
  if (data.rowHeight === 'auto' || !data.isIconView) {
    pagingList.value.forEach((item: any) => {
      item.rowHeight = 'auto';
    });
    data.rowHeight = `${data?.resource_ids?.length * 30}px`;
  }
  else {
    pagingList.value.forEach((item: any) => {
      item.rowHeight = 'auto';
    });
  }
  if (!data.isIconView) {
    pagingList.value.forEach((item: any) => {
      item.isIconView = false;
    });
    data.isIconView = true;
  }
  else {
    pagingList.value.forEach((item: any) => {
      item.isIconView = false;
    });
  }
};

const clearSidesliderForm = () => {
  resourceIds.value = [];
  curResource.bkAppCode = '';
  manner.value = 'api';
};

const handleHideResourceSlider = () => {
  resourceSliderConf.isShow = false;
  clearSidesliderForm();
};

const handleBindResource = () => {
  confirmLoading.value = true;
  validateForm1.value?.validate().then(() => {
    if (resourceSliderConf.type === 'add') {
      handlerAddPolicy();
    }
    else {
      handlerUpdatePolicy();
    }
  }, () => {
    confirmLoading.value = false;
  });
};

// 接口数组转换
const yamlConvertJson = (yamlStr: any) => {
  const yamlData = yaml2Json(yamlStr).data || { exempted_apps: [] };
  const { exempted_apps: list } = yamlData;
  if (list.length) {
    dataList.value = list.map((item: any) => {
      return {
        bk_app_code: item.bk_app_code,
        dimension: item.dimension,
        resource_ids: item.resource_ids,
        rowHeight: 'auto',
        isIconView: false,
      };
    });
    // 排序
    dataList.value.sort((a: any, b: any) => {
      return (`${a.bk_app_code}`).localeCompare(b.bk_app_code);
    });
  }
  getTableData();
};

const jsonConvertYaml = () => {
  const mapList = dataList.value.map((item: any) => {
    return {
      bk_app_code: item.bk_app_code,
      dimension: item.dimension,
      resource_ids: item.resource_ids,
    };
  });
  const jsonStr = JSON.stringify({ exempted_apps: mapList });

  return json2Yaml(jsonStr);
};

const sendPolicyData = () => {
  return jsonConvertYaml();
};

const deleteInBatchesPolicy = () => {
  dataList.value = dataList.value?.filter((x: any) => {
    return !whiteListPolicyList.value.some((item: any) => x.bk_app_code === item.bk_app_code);
  });
  whiteListPolicyList.value = [];
  getTableData();
};

const handlerDeletePolicy = (data: any) => {
  for (let i = 0; i < dataList.value.length; i++) {
    if (dataList.value[i].bk_app_code === data.bk_app_code) {
      dataList.value.splice(i, 1);
      break;
    }
  }
  getSearchDataList();
  getTableData();
  Message({
    theme: 'success',
    message: t('删除成功'),
  });
};

const handlerUpdatePolicy = () => {
  const dimension = manner.value;
  const ids = dimension === 'api' ? [] : resourceIds.value;
  dataList.value.forEach((item: any) => {
    if (item.bk_app_code === curResource.bkAppCode) {
      item.dimension = dimension;
      item.resource_ids = ids;
    }
  });
  handleHideResourceSlider();
  getTableData();
  Message({
    theme: 'success',
    message: t('编辑成功'),
  });
  confirmLoading.value = false;
};

const handlerAddPolicy = () => {
  const dimension = manner.value;
  const ids = dimension === 'api' ? [] : resourceIds.value;
  dataList.value.push({
    bk_app_code: curResource.bkAppCode,
    dimension,
    resource_ids: ids,
    rowHeight: 'auto',
    isIconView: false,
  });
  handleHideResourceSlider();
  getTableData();
  Message({
    theme: 'success',
    message: t('新增成功'),
  });
  confirmLoading.value = false;
};

const handleResourceChange = (sourceList: any, targetList: any, targetValueList: any) => {
  resourceIds.value = targetValueList;
};

const handleResourceSelect = ({ row, checked }: any) => {
  if (checked) { // 选中单行
    whiteListPolicyList.value?.push(row);
  }
  else { // 取消选中
    whiteListPolicyList.value = whiteListPolicyList.value?.filter((item: any) => {
      return item?.bk_app_code !== row.bk_app_code;
    });
  }
};

const handleSelectAll = ({ checked, data }: any) => {
  if (checked) {
    whiteListPolicyList.value = data;
  }
  else {
    whiteListPolicyList.value = [];
  }
};

const sidesliderHidden = () => {
  clearSidesliderForm();
  removeResourceScroll();
};

const handleBatchRemovePolicy = () => {
  if (!whiteListPolicyList.value?.length) {
    Message({
      theme: 'error',
      message: t('请选择要删除的白名单'),
    });
    return false;
  }

  InfoBox({
    title: t('确认要批量删除白名单？'),
    onConfirm() {
      deleteInBatchesPolicy();
    },
  });
};

const handlePageLimitChange = (limit: number) => {
  pagination.limit = limit;
  pagination.current = 1;
  getTableData();
};

const handlePageChange = (newPage: number) => {
  pagination.current = newPage;
  getTableData();
};

const getTableData = () => {
  isTableLoading.value = true;
  let pageSize = Math.ceil(dataList.value.length / pagination.limit);
  let tableDataList = dataList.value;
  // 筛选条件数据
  if (searchParams.value.bk_app_code || searchParams.value.resource_id) {
    tableDataList = searchList.value;
    pageSize = Math.ceil(searchList.value.length / pagination.limit);
  }
  if (pageSize < pagination.current) {
    pagination.current = pageSize;
  }
  if (pagination.current < 1) {
    pagination.current = 1;
  }
  const startCurrent = pagination.current - 1;
  pagingList.value = tableDataList?.slice(
    startCurrent < 0 ? 0 : startCurrent * pagination.limit,
    pagination.current * pagination.limit,
  );
  pagination.count = tableDataList?.length || 0;
  // 添加子项
  searchResourceCondition[0].children = tableDataList?.map((item: any) => {
    return {
      id: item.bk_app_code,
      name: item.bk_app_code,
    };
  });
  setTimeout(() => {
    isTableLoading.value = false;
  }, 300);
};

const handleAddResource = () => {
  resourceSliderConf.isShow = true;
  resourceSliderConf.type = 'add';
  resourceSliderConf.title = t('添加白名单');
  resourceTargetList.value = [];
  rules.bkAppCode.push({
    validator: (value: any) => {
      const filterArr = dataList.value.filter((item: any) => item.bk_app_code === value);
      return !filterArr.length;
    },
    message: t('该蓝鲸应用ID白名单已存在'),
    trigger: 'blur',
  });
  handleResourceScroll();
  // const initData = {
  //   ...curResource,
  //   manner: manner.value,
  // };
  // initSidebarFormData(initData);
};

const handleEditResource = (data: any) => {
  resourceSliderConf.isShow = true;
  resourceSliderConf.type = 'edit';
  resourceSliderConf.title = t('编辑白名单');
  curResource.bkAppCode = data.bk_app_code;
  manner.value = data.dimension;
  resourceTargetList.value = data.resource_ids;
  if (rules.bkAppCode.length > 2) {
    rules.bkAppCode.pop();
  }
  handleResourceScroll();
  // 编辑需要添加资源选择对比
  // const initData = {
  //   ...curResource,
  //   manner: manner.value,
  //   resourceIds: resourceIds.value,
  // };
  // initSidebarFormData(initData);
};

const getResourcesData = async () => {
  const query = {
    offset: 0,
    limit: 10000,
  };
  resourceList.value = await getVerifiedUserRequiredResources(gatewayId.value, query);
  searchResourceCondition[1].children = resourceList.value.map((item: any) => {
    return {
      id: item.id,
      name: item.name,
    };
  });
};

const init = () => {
  nextTick(() => {
    getTableData();
  });
  getResourcesData();
};

onMounted(() => {
  dragendColumn();
  getResourcesViewWidth();
});

init();
if (type === 'edit') {
  yamlConvertJson(yamlStr || '');
}

defineExpose({ sendPolicyData });

</script>

<style lang="scss" scoped>
.top-tips {
  font-size: 14px;
  font-weight: bold;
  line-height: 1;
  color: #63656e;
}

.icon-class {
  font-size: 16px;
}

.white-transfer-wrapper {
  padding: 20px;
  padding-bottom: 10px;
  background-color: rgb(244 247 250);
  border: 1px solid #dde4eb;

  .icon-class {
    color: #63656e;
  }

  .tips-text {
    margin-top: 8px;
    font-size: 12px;
    color: #63656e;
  }
}

.play-shape {
  position: relative;
  display: flex;
  width: 100%;
  height: 100%;
  height: 20px;
  font-size: 14px;
  color: #c4c6cc;
  cursor: pointer;
  align-items: center;
  justify-content: center;

  &::before {
    position: absolute;
    padding: 10px;
    content: '';
  }
}

.icon-view {
  transform: rotate(90deg);
  transition: all .3s;
}

.icon-conceal {
  transform: rotate(0deg);
  transition: all .2s;
}

.parent {
  position: relative;
}

.column-wrapper {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.text-view {
  display: block;
  float: left;
  width: 100%;
}

:deep(.bk-table-footer-wrapper) {
  overflow: auto;
}

:deep(.bk-table-header-wrapper) {
  overflow: auto;
}

.transfer-source-item {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
