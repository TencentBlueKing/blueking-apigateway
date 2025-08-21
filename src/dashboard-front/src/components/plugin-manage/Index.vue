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
  <div class="plugin-container">
    <BkLoading :loading="isBindingListLoading">
      <!-- 默认展示 -->
      <template v-if="curBindingPlugins.length === 0">
        <BkException
          v-if="gatewayStore.currentGateway?.kind !== 1"
          :class="{ 'exception-gray': false }"
          class="exception-wrap-item"
          type="empty"
        >
          {{ t('尚未添加插件，') }}
          <BkButton
            v-bk-tooltips="{
              content: t('当前有版本正在发布，请稍后再操作'),
              disabled: getStageStatus(stageData) !== 'doing'
            }"
            :disabled="getStageStatus(stageData) === 'doing'"
            text
            theme="primary"
            @click="handlePluginAdd"
          >
            {{ t('立即添加') }}
          </BkButton>
        </BkException>
        <BkException
          v-else
          type="empty"
        >
          {{ t('尚未添加插件') }}
        </BkException>
      </template>
      <div
        v-else
        class="bindding-info p-10px"
      >
        <div class="pb-12px pl-12px">
          <BkAlert closable>
            {{ t('插件按优先级从高到低排序，多个插件优先级高的先执行。') }}
          </BkAlert>
        </div>
        <BkButton
          v-if="gatewayStore.currentGateway?.kind !== 1"
          v-bk-tooltips="{
            content: t('当前有版本正在发布，请稍后再操作'),
            disabled: getStageStatus(stageData) !== 'doing'
          }"
          :disabled="getStageStatus(stageData) === 'doing'"
          class="add-plugin-btn"
          theme="primary"
          @click="handlePluginAdd"
        >
          <AgIcon
            class="icon pr-10px text-12px"
            name="plus"
          />
          {{ t('添加插件') }}
        </BkButton>
        <BkCollapse
          v-model="activeIndex"
          header-icon="right-shape"
          :list="curBindingPlugins"
          class="binding-plugins mt-20px"
        >
          <template #title="slotProps">
            <span class="text-15px">
              {{ slotProps.name }}
              <template v-if="gatewayStore.currentGateway?.kind !== 1">
                <AgIcon
                  v-bk-tooltips="{
                    content: t('当前有版本正在发布，请稍后再操作'),
                    disabled: getStageStatus(stageData) !== 'doing'
                  }"
                  class="mx-5px"
                  name="edit-line"
                  size="15"
                  @click.stop="() => handleEditPlugin(slotProps)"
                />
                <AgIcon
                  v-bk-tooltips="{
                    content: t('当前有版本正在发布，请稍后再操作'),
                    disabled: getStageStatus(stageData) !== 'doing'
                  }"
                  class="mx-5px"
                  name="delet"
                  size="15"
                  @click.stop="() => handleDeletePlugin(slotProps)"
                />
              </template>
            </span>
          </template>
          <template #content="slotProps">
            <div>
              <ConfigDisplayTable :plugin="slotProps" />
            </div>
          </template>
        </BkCollapse>
      </div>
    </BkLoading>

    <!-- 添加插件 -->
    <BkSideslider
      v-model:is-show="isVisible"
      :title="t('添加插件')"
      quick-close
      ext-cls="plugin-add-slider"
      :width="pluginSliderWidth"
      @closed="isExampleVisible = false"
    >
      <template #default>
        <BkSteps
          :cur-step="state.curStep"
          :steps="state.plugintSteps"
          controllable
          ext-cls="plugin-add-steps"
          @click="stepChanged"
        />
        <div class="plugin-add-container">
          <!-- 选择插件 -->
          <div
            v-if="state.curStep === 1"
            class="plugins px-20px"
          >
            <div class="pt-16px">
              <BkAlert closable>
                {{ t('插件按优先级从高到低排序，多个插件优先级高的先执行。') }}
              </BkAlert>
            </div>
            <div class="plugin-search">
              <BkInput
                v-model="searchValue"
                clearable
                type="search"
                :placeholder="t('请输入插件关键字，按Enter搜索')"
                @enter="handleSearch"
              />
            </div>
            <BkLoading :loading="isPluginListLoading">
              <div class="plugin-list">
                <div
                  v-for="item in pluginListDate"
                  :key="item.id"
                  :class="[isBound(item) ? 'plugin disabled' : 'plugin ']"
                  @click="() => handleChoosePlugin(item)"
                  @mouseenter="() => handlePluginHover((item.code))"
                >
                  <div class="plungin-head">
                    <span
                      v-if="PLUGIN_ICONS.includes(item.code || item.type)"
                      class="plugin-icon"
                    >
                      <svg class="icon svg-icon">
                        <use :xlink:href="`#icon-ag-plugin-${item.code || item.type}`" />
                      </svg>
                    </span>
                    <span
                      v-else
                      class="plugin-icon"
                    >
                      {{ pluginCodeFirst(item.code || item.type) }}
                    </span>
                    <span
                      v-show="isBound(item)"
                      class="bindding-text"
                    >
                      {{ t('已添加') }}
                    </span>
                  </div>
                  <p
                    v-bk-tooltips="{
                      content: t('插件已添加，不能再选择'),
                      disabled: !isBound(item)
                    }"
                    class="plugin-name"
                    :class="[isBound(item) ? 'added' : '']"
                  >
                    {{ item.name }}
                  </p>
                  <div class="binding">
                    <ul class="binding-list">
                      <li>
                        {{ t('版本：') }}<span>V1.0.0</span>
                      </li>
                      <li>
                        {{ t('已绑环境：') }}
                        <BkPopover
                          placement="top"
                          theme="light"
                          width="220"
                          :disabled="item.related_scope_count.stage === 0"
                        >
                          <span :class="[item.related_scope_count.stage === 0 ? 'binding-empty' : 'binding-number',]">
                            {{ item.related_scope_count.stage }}
                          </span>
                          <template #content>
                            <div class="bingding-scope">
                              <p class="scope-header font-bold">
                                {{ t('已绑环境') }}
                              </p>
                              <ul class="scope-list mt-10px">
                                <li
                                  v-for="stageItem in curBindingScopeData.stages"
                                  :key="stageItem.id"
                                  class="scope-li mb-5px"
                                  @mouseenter="handleScopeHover((stageItem.name))"
                                  @mouseleave="handlScopeLeave"
                                  @click="handeleJumpStage(stageItem)"
                                >
                                  {{ stageItem.name }}
                                  <AgIcon
                                    v-if="stageItem.name === curHover"
                                    class="icon ml-5px"
                                    name="jump"
                                  />
                                </li>
                              </ul>
                            </div>
                          </template>
                        </BkPopover>
                      </li>
                      <li>
                        {{ t('已绑资源：') }}
                        <BkPopover
                          placement="top"
                          theme="light"
                          width="420"
                          :disabled="item.related_scope_count.resource === 0"
                        >
                          <span
                            :class="[item.related_scope_count.resource === 0 ? 'binding-empty' : 'binding-number',]"
                          >
                            {{ item.related_scope_count.resource }}
                          </span>
                          <template #content>
                            <div class="bingding-scope">
                              <p class="scope-header font-bold">
                                {{ t('已绑资源') }}
                              </p>
                              <ul class="scope-list mt-10px ">
                                <li
                                  v-for="resourceItem in curBindingScopeData.resources"
                                  :key="resourceItem.id"
                                  class="scope-li mb-5px"
                                  @mouseenter="handleScopeHover((resourceItem.name))"
                                  @mouseleave="handlScopeLeave"
                                  @click="handeleJumpResource(resourceItem)"
                                >
                                  {{ resourceItem.name }}
                                  <AgIcon
                                    v-if="resourceItem.name === curHover"
                                    class="icon ml-5px"
                                    name="jump"
                                  />
                                </li>
                              </ul>
                            </div>
                          </template>
                        </BkPopover>
                      </li>
                    </ul>
                  </div>
                  <div class="plugin-notes">
                    {{ item.notes }}
                  </div>
                  <div
                    v-show="curChooseCode === item.code"
                    class="plugin-chose"
                  >
                    <div class="icon apigateway-icon icon-ag-check-1 choose-icon" />
                  </div>
                </div>
              </div>
              <TableEmpty
                v-if="!pluginListDate.length"
                :empty-type="tableEmptyConf.emptyType"
                :abnormal="tableEmptyConf.isAbnormal"
                @refresh="handleSearch"
                @clear-filter="handleClearFilterKey"
              />
            </BkLoading>
          </div>
          <!-- 配置插件 -->
          <div
            v-else
            class="px-40px py-20px"
          >
            <PluginInfo
              v-model:show-example="isExampleVisible"
              :cur-plugin="curChoosePlugin"
              :scope-info="curScopeInfo"
              :type="curType"
              :plugin-list="pluginListDate"
              :binding-plugins="curBindingPlugins"
              @choose-plugin="handleChoosePlugin"
              @on-change="handleOperate"
            />
          </div>
        </div>
      </template>
      <template
        v-if="state.curStep === 1"
        #footer
      >
        <div class="slider-footer">
          <div class="fist-step">
            <BkButton
              theme="primary"
              :disabled="!curChoosePlugin"
              @click="handelNext"
            >
              {{ t('下一步') }}
            </BkButton>
            <BkButton @click="handleCancel">
              {{ t('取消') }}
            </BkButton>
          </div>
        </div>
      </template>
    </BkSideslider>

    <!-- 修改插件 -->
    <BkSideslider
      v-model:is-show="isEditVisible"
      :title="t('修改插件')"
      quick-close
      ext-cls="plugin-add-slider"
      :width="pluginSliderWidth"
      @closed="isExampleVisible = false"
    >
      <template #default>
        <div class="px-40px py-20px">
          <PluginInfo
            v-model:show-example="isExampleVisible"
            :cur-plugin="curChoosePlugin"
            :scope-info="curScopeInfo"
            :edit-plugin="curEditPlugin"
            :type="curType"
            @on-change="handleOperate"
          />
        </div>
      </template>
    </BkSideslider>
  </div>
</template>

<script setup lang="ts">
import PluginInfo from './PluginInfo.vue';
import TableEmpty from '@/components/table-empty/Index.vue';
import {
  InfoBox,
  Message,
} from 'bkui-vue';
import {
  useGateway,
  useStage,
} from '@/stores';
import {
  deletePluginConfig,
  getPluginBindingsList,
  getPluginConfig,
  getPluginListData,
  getScopeBindingPluginList,
} from '@/services/source/plugin-manage';
import ConfigDisplayTable from './ConfigDisplayTable.vue';
import { getStageStatus } from '@/utils';
import { useRouteParams } from '@vueuse/router';
import { PLUGIN_ICONS } from '@/constants';

interface IProps {
  resourceId?: number
  stageId: number
}

const {
  resourceId = 0,
  stageId,
} = defineProps<IProps>();

const emit = defineEmits<{
  'on-jump': [id: any]
  'on-update-plugin': [void]
}>();

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const gatewayStore = useGateway();
const stageStore = useStage();
// 网关id
const gatewayId = useRouteParams('id', 0, { transform: Number });

const scopeType = ref('');
const scopeId = ref(-1);
const isBindingListLoading = ref(false);
const isPluginListLoading = ref(false);
const isVisible = ref(false);
const curType = ref('');
const isEditVisible = ref(false);
const isAddSuccess = ref(false);
const searchValue = ref('');
const pluginListDate = ref([]);
const curBindingScopeData = ref<any>({});
const curHover = ref('');
const curBindingPlugins = ref<any>([]);
const curChoosePlugin = ref(null);
const curChooseCode = ref('');
const curEditPlugin = ref<any>({});
const curScopeInfo = reactive({
  scopeType: '',
  scopeId: -1,
  apigwId: -1,
});
const state = reactive({
  plugintSteps: [
    {
      title: t('选择插件'),
      icon: 1,
    },
    {
      title: t('配置插件'),
      icon: 2,
    },
  ],
  curStep: 1,
});
const tableEmptyConf = ref({
  emptyType: '',
  isAbnormal: false,
});
// PluginInfo 中的插件示例是否可见
const isExampleVisible = ref(false);

const activeIndex = ref<number[]>([]);

const pluginDeleting = ref(false);

// 控制插件 slider 宽度，会在展示插件使用示例时变宽
const pluginSliderWidth = computed(() => isExampleVisible.value ? 1360 : 960);

// 当前环境信息
const stageData = computed(() => {
  if (stageStore.curStageData.id !== null) {
    return stageStore.curStageData;
  }
  return {
    name: '',
    description: '',
    description_en: '',
    status: 1,
    created_time: '',
    release: {
      status: '',
      created_time: null,
      created_by: '',
    },
    resource_version: '',
    new_resource_version: '',
    publish_validate_msg: '',
  };
});

const pluginCodeFirst = computed(() => {
  return function (code: string) {
    if (code.startsWith('bk-')) {
      return code.charAt(3).toUpperCase();
    }
    return code.charAt(0).toUpperCase();
  };
});

const isBound = computed(() => {
  return function (obj: any) {
    return curBindingPlugins.value.some((item: { code: string }) => item.code === obj.code);
  };
});

watch(curBindingPlugins, () => {
  activeIndex.value = Object.keys(curBindingPlugins.value)?.map((item: string) => Number(item)) || [];
});

watch(
  [
    () => stageId,
    () => resourceId,
  ],
  () => {
    init();
  },
);

watch(searchValue, async (v) => {
  // 清空搜索框
  if (!v) {
    const params = {
      scope_type: scopeType.value,
      scope_id: scopeId.value,
    };
    await getPluginListDetails(params);
  }
});

// 监听是否成功添加
watch(
  () => isAddSuccess.value,
  (newVal) => {
    if (newVal) {
      init();
    }
  },
  { immediate: true },
);

const stepChanged = (index: number) => {
  if (index === 1) {
    state.curStep = index;
  }
  if (index === 2) {
    if (curChoosePlugin.value) {
      state.curStep = index;
    }
    else {
      Message({
        theme: 'warning',
        message: '请先勾选插件',
      });
    }
  }
};

const handleOperate = (operate: string) => {
  switch (operate) {
    case 'pre':
      state.curStep = 1;
      break;
    case 'addCancel':
      resetData();
      break;
    case 'editCancel':
      isEditVisible.value = false;
      break;
    case 'addSuccess':
      resetData();
      isAddSuccess.value = true;
      emit('on-update-plugin');
      break;
    case 'editSuccess':
      getBindingDetails();
      isEditVisible.value = false;
      emit('on-update-plugin');
      break;
    default:
      break;
  }
};

// hover插件获取其对应绑定的stage和resource数量
const handlePluginHover = async (itemCode: string) => {
  const flag = curBindingPlugins.value.some((item: { code: string }) => item.code === itemCode);
  if (flag) return;
  try {
    const res = await getPluginBindingsList(gatewayId.value, itemCode);
    curBindingScopeData.value = res;
  }
  catch (error) {
    console.log('error', error);
  }
};

// hover已绑stage或resource数量
const handleScopeHover = (name: string) => {
  curHover.value = name;
};
const handlScopeLeave = () => {
  curHover.value = '';
};

const handleClearFilterKey = () => {
  searchValue.value = '';
  // handleSearch();
};

// 编辑插件
const handleEditPlugin = async (item: any) => {
  if (getStageStatus(stageData.value) === 'doing') {
    return;
  }
  curType.value = 'edit';
  const { code, config_id } = item;
  const curEditItem = curBindingPlugins.value.find((pluginItem: { code: string }) => pluginItem.code === code);
  curEditPlugin.value = await getPluginConfig(
    gatewayId.value,
    scopeType.value,
    scopeId.value,
    code,
    config_id,
  );
  curChoosePlugin.value = curEditItem;
  isEditVisible.value = true;
};

// 删除插件
const handleDeletePlugin = (item: any) => {
  if (getStageStatus(stageData.value) === 'doing') {
    return;
  }
  const { code, config_id } = item;
  InfoBox({
    title: t('确定停用插件？'),
    infoType: 'warning',
    subTitle: t('将删除相关配置，不可恢复，请确认是否删除'),
    confirmText: t('停用'),
    cancelText: t('取消'),
    onConfirm: async () => {
      if (pluginDeleting.value) {
        return;
      }
      pluginDeleting.value = true;
      try {
        await deletePluginConfig(gatewayId.value, scopeType.value, scopeId.value, code, config_id);
        Message({
          message: t('停用成功'),
          theme: 'success',
          width: 'auto',
        });
        emit('on-update-plugin');
        init();
      }
      finally {
        setTimeout(() => {
          pluginDeleting.value = false;
        }, 300);
      }
    },
  });
};

// 跳转stage
const handeleJumpStage = (item: any) => {
  const { name } = item;
  const isRouteStage = route.path.includes('stage');
  const query = { stage: name };
  if (isRouteStage) {
    router.push({ query });
  }
  else {
    router.push({
      name: 'apigwStagePluginManage',
      params: { id: gatewayId.value },
      query,
    });
  }
};
// 跳转resource
const handeleJumpResource = (item: any) => {
  const { id } = item;
  const isRouteStage = route.path.includes('stage');
  if (isRouteStage) {
    router.push({
      name: 'ResourceSetting',
      params: { id: gatewayId.value },
    });
  }
  emit('on-jump', id);
};

function init() {
  const isStage = route.path.includes('stage');
  scopeType.value = isStage ? 'stage' : 'resource';
  scopeId.value = isStage ? stageId : resourceId;
  curScopeInfo.scopeType = scopeType.value;
  curScopeInfo.scopeId = scopeId.value;
  curScopeInfo.apigwId = gatewayId.value;
  const params = {
    scope_type: scopeType.value,
    scope_id: scopeId.value,
  };

  if (!scopeId.value) return;
  getBindingDetails();
  getPluginListDetails(params);
}

const resetData = () => {
  curChoosePlugin.value = null;
  isVisible.value = false;
  state.curStep = 1;
  searchValue.value = '';
  curChooseCode.value = '';
};

// 获取已绑定插件列表
async function getBindingDetails() {
  try {
    isBindingListLoading.value = true;
    // 当前环境或资源绑定的插件
    curBindingPlugins.value = await getScopeBindingPluginList(gatewayId.value, scopeType.value, scopeId.value);
  }
  finally {
    isBindingListLoading.value = false;
  }
}

// 获取可配置的插件列表
async function getPluginListDetails(params: {
  scope_type: string
  scope_id: number
  keyword?: string
}) {
  try {
    isPluginListLoading.value = true;
    const res = await getPluginListData(gatewayId.value, params);
    pluginListDate.value = res.results || [];
  }
  catch (error) {
    pluginListDate.value = [];
    tableEmptyConf.value.isAbnormal = true;
    console.log('error', error);
  }
  finally {
    isPluginListLoading.value = false;
  }
}

// 立即添加
const handlePluginAdd = () => {
  resetData();
  curType.value = 'add';
  isVisible.value = true;
  isAddSuccess.value = false;
};

// 选择插件
const handleChoosePlugin = (obj: any) => {
  const flag = curBindingPlugins.value.some((item: { code: string }) => item.code === obj.code);
  if (flag) {
    return;
  }
  curChooseCode.value = obj.code;
  curChoosePlugin.value = obj;
};

// enter搜索
const handleSearch = async (keyword?: string) => {
  searchValue.value = keyword || '';
  const params = {
    keyword,
    scope_type: scopeType.value,
    scope_id: scopeId.value,
  };
  try {
    await getPluginListDetails(params);
    updateTableEmptyConfig();
    tableEmptyConf.value.isAbnormal = false;
  }
  catch (error) {
    console.log('error', error);
    tableEmptyConf.value.isAbnormal = false;
  }
};

// 下一页
const handelNext = () => {
  state.curStep = 2;
};

// 取消添加
const handleCancel = () => {
  resetData();
};

const updateTableEmptyConfig = () => {
  if (searchValue.value || !pluginListDate.value.length) {
    tableEmptyConf.value.emptyType = 'searchEmpty';
    return;
  }
  if (searchValue.value) {
    tableEmptyConf.value.emptyType = 'empty';
    return;
  }
  tableEmptyConf.value.emptyType = '';
};

init();

</script>

<style lang="scss" scoped>
.plugin-container {

  :deep(.bk-exception-page) {
    height: 420px;
    justify-content: center;

    .bk-exception-img {
      width: 220px;
      height: 130px;
    }

    .bk-exception-footer {
      margin-top: 0;
    }
  }
}

.plugin-add-steps {
  width: 400px;
  margin: 20px auto;
}

.plugin-add-container {
  min-height: calc(100vh - 170px) !important;
  border-top: 1px solid #e3e3e5;
}

.plugins {
  min-height: calc(100vh - 171px) !important;
  background-color: #f5f7fb;

  .plugin-search {
    padding: 12px 0 20px;

    .bk-input--default {
      width: 608px;
    }
  }

  .plugin-list {
    display: flex;
    flex-wrap: wrap;

    .plugin {
      position: relative;
      width: 32%;
      padding: 24px 20px 20px 24px;
      margin-right: 18px;
      margin-bottom: 20px;
      overflow: hidden;
      cursor: pointer;
      background-color: #fff;
      border-radius: 12px;
      box-shadow: 0 2px 4px 0 #1919290d;

      &:hover {
        box-shadow: 0 2px 4px 0 rgb(25 25 41 / 25.1%);
      }

      .plungin-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;

        .plugin-icon {
          display: inline-block;
          width: 48px;
          height: 48px;
          font-size: 24px;
          font-weight: 700;
          line-height: 48px;
          color: #3a84f6;
          text-align: center;
          background-color: #e2edfd;
          border-radius: 50%;

          .svg-icon {
            width: 48px;
            height: 48px;
          }
        }

        .bindding-text {
          font-size: 12px;
          color: #c4c6cc;
        }
      }

      .plugin-name {
        font-size: 14px;
        font-weight: 700;
        color: #313238;

        &.added {
          position: relative;
          z-index: 2;
          display: inline-block;
          cursor: not-allowed;
          opacity: 50%;
        }
      }

      .binding {

        .binding-list {
          display: flex;
          margin: 4px 0 12px;
          font-size: 12px;
          color: #979ba5;
          justify-content: space-between;

          .binding-empty {
            font-weight: 700;
            color: #64666a;
          }

          .binding-number {
            font-weight: 700;
            color: #4482e4;
          }

        }
      }

      .plugin-notes {
        font-size: 12px;
        line-height: 22px;
        color: #63656e;
      }

      .plugin-chose {
        position: absolute;
        top: 0;
        right: 0;
        width: 0;
        height: 0;
        border-top: 45px solid #3B83FC;
        border-left: 45px solid transparent;

        .choose-icon {
          position: absolute;
          top: -41px;
          right: 7px;
          width: 20px;
          height: 20px;
          font-size: 26px;
          line-height: 20px;
          color: #fff;
          text-align: center;
          border-radius: 50%;
        }
      }
    }

    .plugin:nth-child(3n) {
      margin-right: 0;
    }

    .disabled::after {
      position: absolute;
      top: 0;
      left: 0;
      z-index: 1;
      width: 100%;
      height: 100%;
      cursor: not-allowed;
      background-color: rgb(250 252 254 / 50%);
      border-radius: 12px;
      content: "";
      user-select: none;
    }
  }
}

.bingding-scope {
  padding: 5px;

  .scope-list {
    margin-left: 17px;

    :deep(.scope-li) {
      list-style: disc !important;
      cursor: pointer;
    }

    .scope-li:hover {
      color: #4B85E5;
    }
  }
}

.bindding-info {
  min-height: 480px;

  .add-plugin-btn {
    margin-left: 12px;

    .icon-ag-plus {
      font-weight: 700;
    }
  }

}

.plugin-add-slider {

  :deep(.bk-modal-content) {
    // height: calc(100vh - 106px) !important;
    // height: calc(100% - 126px) !important;
    overflow-y: auto;
  }

  :deep(.bk-sideslider-footer) {
    height: 48px !important;
  }

  .slider-footer {
    display: flex;
    align-items: center;
    padding: 0 24px;

    .fist-step {
      font-size: 0;

      .bk-button {
        min-width: 88px;

        &:not(&:first-child) {
          margin-left: 8px;
        }
      }
    }
  }
}

.binding-plugins {

  .apigateway-icon:hover {
    color: #1768ef;
  }
}

:deep(.bk-collapse-icon-left) {

  .bk-collapse-icon {
    top: 15px;
    left: 16px;
  }

  .bk-collapse-item {
    margin-bottom: 5px;
  }
}

:deep(.bk-collapse-icon) {

  svg {
    font-size: 16px;
  }
}

:deep(.bk-collapse-header) {

  .bk-collapse-title {
    font-weight: 700;
  }
}

:deep(.bk-collapse-header):hover {
  background-color: #fff !important;
}

.form-key-cls {
  width: 170px;
  padding: 5px 0;
  font-size: 12px;
  color: #63656E;
  text-align: right;
}

.form-val-cls {
  font-size: 12px;
  color: #313238;
}
</style>
