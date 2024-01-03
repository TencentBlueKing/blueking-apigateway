<template>
  <div class="plugin-container">
    <bk-loading :loading="isBindingListLoading">
      <!-- 默认展示 -->
      <bk-exception
        class="exception-wrap-item" type="empty" :class="{ 'exception-gray': false }"
        v-if="curBindingPlugins.length === 0">
        {{ t('尚未添加插件，') }}
        <bk-button text theme="primary" @click="handlePluginAdd">
          {{ t('立即添加') }}
        </bk-button>
      </bk-exception>
      <div class="bindding-info p10" v-else>
        <bk-button class="add-plugin-btn" @click="handlePluginAdd">
          <i class="icon apigateway-icon icon-ag-plus pr10 f12"></i>
          {{ t('添加插件') }}
        </bk-button>
        <bk-collapse header-icon="right-shape" :list="curBindingPlugins" class="binding-plugins mt20">
          <template #title="slotProps">
            <span class="f15" @mouseenter="handleTitleHover(slotProps)" @mouseleave="handleTitleLeave">
              {{ slotProps.name }}
              <span
                class="icon apigateway-icon icon-ag-edit-line ml5 mr5 " @click.stop="handleEditePlugin(slotProps)"
                v-if="slotProps.name === curHoverHead">
              </span>
              <span
                class="icon apigateway-icon icon-ag-delet " @click="handleDeletePlugin(slotProps)"
                v-if="slotProps.name === curHoverHead">
              </span>
            </span>
          </template>
          <template #content="slotProps">
            <div>
              <!-- {{ slotProps.config }} -->
              <div v-for="(item, key) in slotProps.config" :key="key">
                <div class="flex-row align-items-center">
                  <div class="form-key-cls">{{key}}：</div>
                  <div class="form-val-cls">{{item || '--'}}</div>
                </div>
              </div>
            </div>
          </template>
        </bk-collapse>
      </div>
    </bk-loading>

    <!-- 添加插件 -->
    <bk-sideslider v-model:isShow="isVisible" :title="t('添加插件')" quick-close ext-cls="plugin-add-slider" width="960">
      <template #default>
        <bk-steps :cur-step="state.curStep" :steps="state.plugintSteps" ext-cls="plugin-add-steps" />
        <div class="plugin-add-container">
          <!-- 选择插件 -->
          <div class="plugins pl20 pr20" v-if="state.curStep === 1">
            <div class="plugin-search">
              <bk-input
                v-model="searchValue" clearable type="search" :placeholder="t('请输入插件关键字，按Enter搜索')"
                @enter="handleSearch" @clear="handleClear" />
            </div>
            <bk-loading :loading="isPluginListLoading">
              <div class="plugin-list">
                <div
                  :class="[isBound(item) ? 'plugin disabled' : 'plugin ']" v-for="item in pluginListDate"
                  :key="item.id" @click="handleChoosePlugin(item)" @mouseenter="handlePluginHover((item.code))">
                  <div class="plungin-head">
                    <span class="plugin-icon">
                      {{ pluginCodeFirst(item.code) }}
                    </span>
                    <span v-show="isBound(item)" class="binddingText">
                      {{ t('已添加') }}
                    </span>
                  </div>
                  <p class="plugin-name">{{ item.name }}</p>
                  <div class="binding">
                    <ul class="binding-list">
                      <li>
                        {{ t('版本：') }}<span>{{ t('V1.0.0') }}</span>
                      </li>
                      <li>
                        {{ t('已绑环境：') }}
                        <bk-popover
                          placement="top" theme="light" width="220"
                          :disabled="item.related_scope_count.stage === 0">
                          <span :class="[item.related_scope_count.stage === 0 ? 'binding-empty' : 'binding-number',]">
                            {{ item.related_scope_count.stage }}
                          </span>
                          <template #content>
                            <div class="bingding-scope">
                              <p class="scope-header fw700">{{ t('已绑环境') }}</p>
                              <ul class="scope-list mt10">
                                <li
                                  class="scope-li mb5" @mouseenter="handleScopeHover((stageItem.name))"
                                  @mouseleave="handlScopeLeave" @click="handeleJumpStage(stageItem)"
                                  v-for="stageItem in curBindingScopeData.stages" :key="stageItem.id">
                                  {{ stageItem.name }}
                                  <span
                                    class="icon apigateway-icon icon-ag-jump ml5"
                                    v-if="stageItem.name === curHover">
                                  </span>
                                </li>
                              </ul>
                            </div>
                          </template>
                        </bk-popover>
                      </li>
                      <li>
                        {{ t('已绑资源：') }}
                        <bk-popover
                          placement="top" theme="light" width="420"
                          :disabled="item.related_scope_count.resource === 0">
                          <span
                            :class="[item.related_scope_count.resource === 0 ? 'binding-empty' : 'binding-number',]">
                            {{ item.related_scope_count.resource }}
                          </span>
                          <template #content>
                            <div class="bingding-scope">
                              <p class="scope-header fw700">{{ t('已绑资源') }}</p>
                              <ul class="scope-list mt10 ">
                                <li
                                  class="scope-li mb5" @mouseenter="handleScopeHover((resourceItem.name))"
                                  @mouseleave="handlScopeLeave" @click="handeleJumpResource(resourceItem)"
                                  v-for="resourceItem in curBindingScopeData.resources" :key="resourceItem.id">
                                  {{ resourceItem.name }}
                                  <span
                                    class="icon apigateway-icon icon-ag-jump ml5"
                                    v-if="resourceItem.name === curHover">
                                  </span>
                                </li>
                              </ul>
                            </div>
                          </template>
                        </bk-popover>
                      </li>
                    </ul>
                  </div>
                  <div class="plugin-notes">
                    {{ item.notes }}
                  </div>
                  <div class="plugin-chose" v-show="curChooseCode === item.code">
                    <div class="icon apigateway-icon icon-ag-check-1 choose-icon"></div>
                  </div>
                </div>
              </div>
            </bk-loading>

          </div>
          <!-- 配置插件 -->
          <div class="plugin-config pl40 pr40 pt20 pb20" v-else>
            <pluginInfo
              :cur-plugin="curChoosePlugin" :scope-info="curScopeInfo" :type="curType"
              @on-change="handleOperate">
            </pluginInfo>
          </div>
        </div>
      </template>
      <template #footer v-if="state.curStep === 1">
        <div class="slider-footer pl20">
          <div class="fist-step">
            <bk-button theme="primary" @click="handelNext" width="50px" :disabled="!curChoosePlugin">
              {{ t('下一步') }}
            </bk-button>
            <bk-button @click="handleCancel">{{ t('取消') }}</bk-button>
          </div>
        </div>
      </template>
    </bk-sideslider>

    <!-- 修改插件 -->
    <bk-sideslider
      v-model:isShow="isEditVisible"
      :title="t('修改插件')"
      quick-close ext-cls="plugin-add-slider"
      width="960">
      <template #default>
        <div class="plugin-config pl40 pr40 pt20 pb20">
          <pluginInfo
            :cur-plugin="curChoosePlugin" :scope-info="curScopeInfo" :edit-plugin="curEditPlugin"
            :type="curType" @on-change="handleOperate">
          </pluginInfo>
        </div>
      </template>
    </bk-sideslider>
  </div>
</template>

<script setup lang="ts">
import pluginInfo from './plugin-info.vue';
import { InfoBox, Message } from 'bkui-vue';
import { ref, reactive, computed, watch, defineEmits } from 'vue';
import { useI18n } from 'vue-i18n';
import { useCommon, useStage } from '@/store';
import { useRoute, useRouter } from 'vue-router';
import {
  getPluginListData,
  getPluginBindingsList,
  getScopeBindingPluginList,
  getPluginConfig,
  deletePluginConfig,
} from '@/http';

const props = defineProps({
  resourceId: {
    type: Number,
    default: 0,
  },
});
const { t } = useI18n();
const emit = defineEmits(['on-jump']);
const route = useRoute();
const router = useRouter();
const common = useCommon();
const stage = useStage();

const { apigwId } = common; // 网关id
const { curStageId } = stage; // 当前stage_id

const scopeType = ref<string>('');
const scopeId = ref<number>(-1);
const isBindingListLoading = ref(false);
const isPluginListLoading = ref(false);
const isVisible = ref(false);
const curType = ref<string>('');
const isEditVisible = ref(false);
const isAddSuccess = ref(false);
const searchValue = ref<string>('');
const pluginListDate = ref<any>({});
const curBindingScopeData = ref<any>({});
const curHover = ref<string>('');
const curHoverHead = ref<string>('');
const curBindingPlugins = ref<any>([]);
const curChoosePlugin = ref(null);
const curChooseCode = ref<string>('');
const curEditPlugin = ref<any>({});
const curScopeInfo = reactive({
  scopeType: '',
  scopeId: -1,
  apigwId: -1,
});
const state = reactive({
  plugintSteps: [
    { title: t('选择插件'), icon: 1 },
    { title: t('配置插件'), icon: 2 },
  ],
  curStep: 1,
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
      break;
    case 'editSuccess':
      isEditVisible.value = false;
      break;
    default:
      break;
  }
};

const pluginCodeFirst = computed(() => {
  return function (code: string) {
    return code.charAt(3).toUpperCase();
  };
});

const isBound = computed(() => {
  return function (obj: any) {
    const flag = curBindingPlugins.value.some((item: { code: string; }) => item.code === obj.code);
    return flag;
  };
});
// hover插件获取其对应绑定的stage和resource数量
const handlePluginHover = async (itemCode: string) => {
  const flag = curBindingPlugins.value.some((item: { code: string; }) => item.code === itemCode);
  if (flag) return;
  try {
    const res = await getPluginBindingsList(apigwId, itemCode);
    curBindingScopeData.value = res;
  } catch (error) {
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

// hover 已绑插件的title
const handleTitleHover = (data: any) => {
  curHoverHead.value = data.name;
};
const handleTitleLeave = () => {
  curHoverHead.value = '';
};

// 编辑插件
const handleEditePlugin = async (item: any) => {
  curType.value = 'edit';
  const { code, config_id } = item;
  console.log(item);
  console.log(pluginListDate.value);
  const curEditItem = pluginListDate.value.find((pluginItem: { code: string; }) => pluginItem.code === code);
  curChoosePlugin.value = curEditItem;
  try {
    const res = await getPluginConfig(apigwId, scopeType.value, scopeId.value, code, config_id);
    curEditPlugin.value = res;
    isEditVisible.value = true;
  } catch (error) {
    console.log('error', error);
  }
};
// 删除插件
const handleDeletePlugin = (item: any) => {
  console.log(item);
  const { code, config_id } = item;
  InfoBox({
    title: t('确定停用插件？'),
    infoType: 'warning',
    subTitle: t('将删除相关配置，不可恢复，请确认是否删除'),
    confirmText: t('停用'),
    cancelText: t('取消'),
    onConfirm: async () => {
      try {
        await deletePluginConfig(apigwId, scopeType.value, scopeId.value, code, config_id);
        Message({
          message: t('停用成功'),
          theme: 'success',
        });
        init();
      } catch (error) {
        console.log('error', error);
      }
    },
  });
};

// 跳转stage
const handeleJumpStage = (item: any) => {
  const { name } = item;
  console.log(item, name);
  const isRouteStage = route.path.includes('stage');
  const query = {
    stage: name,
  };
  if (isRouteStage) {
    router.push({
      query,
    });
  } else {
    router.push({
      name: 'apigwStagePluginManage',
      params: {
        id: apigwId,
      },
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
      name: 'apigwResource',
      params: {
        id: apigwId,
      },
    });
  }
  emit('on-jump', id);
};

const init = () => {
  const isStage = route.path.includes('stage');
  scopeType.value = isStage ? 'stage' : 'resource';
  scopeId.value = isStage ? curStageId : props.resourceId;
  curScopeInfo.scopeType = scopeType.value;
  curScopeInfo.scopeId = scopeId.value;
  curScopeInfo.apigwId = apigwId;
  const params = {
    scope_type: scopeType.value,
    scope_id: scopeId.value,
  };
  getBindingDetails();
  getPluginListDetails(params);
};
const resetData = () => {
  curChoosePlugin.value = null;
  isVisible.value = false;
  state.curStep = 1;
  searchValue.value = '';
  curChooseCode.value = '';
};

// 获取已绑定插件列表
const getBindingDetails = async () => {
  try {
    isBindingListLoading.value = true;
    // 当前环境或资源绑定的插件
    const res = await getScopeBindingPluginList(apigwId, scopeType.value, scopeId.value);
    curBindingPlugins.value = res;
    console.log(curBindingPlugins.value);
  } catch (error) {
    console.log('error', error);
  } finally {
    isBindingListLoading.value = false;
  }
};

// 获取可配置的插件列表
const getPluginListDetails = async (params: { scope_type: string; scope_id: number; keyword?: string; }) => {
  try {
    isPluginListLoading.value = true;
    const res = await getPluginListData(apigwId, params);
    pluginListDate.value = res.results;
    console.log(pluginListDate.value);
  } catch (error) {
    console.log('error', error);
  } finally {
    isPluginListLoading.value = false;
  }
};

// 立即添加
const handlePluginAdd = () => {
  resetData();
  curType.value = 'add';
  isVisible.value = true;
  isAddSuccess.value = false;
};

// 选择插件
const handleChoosePlugin = (obj: any) => {
  const flag = curBindingPlugins.value.some((item: { code: string; }) => item.code === obj.code);
  if (flag) {
    return;
  }
  curChooseCode.value = obj.code;
  curChoosePlugin.value = obj;
  console.log(curChoosePlugin.value);
};
// enter搜索
const handleSearch = () => {
  const params = {
    scope_type: scopeType.value,
    scope_id: scopeId.value,
    keyword: searchValue.value,
  };
  try {
    getPluginListDetails(params);
  } catch (error) {
    console.log('error', error);
  }
};
// 清空搜索框
const handleClear = () => {
  const params = {
    scope_type: scopeType.value,
    scope_id: scopeId.value,
  };
  getPluginListDetails(params);
};
// 下一页
const handelNext = () => {
  state.curStep = 2;
};

// 取消添加
const handleCancel = () => {
  resetData();
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
  background-color: #f5f7fb;
  min-height: calc(100vh - 171px) !important;

  .plugin-search {
    padding: 20px 0px;

    .bk-input--default {
      width: 608px;
    }
  }

  .plugin-list {
    display: flex;
    flex-wrap: wrap;

    .plugin {
      position: relative;
      cursor: pointer;
      margin-right: 18px;
      margin-bottom: 20px;
      width: 32%;
      padding: 20px;
      background-color: #fff;
      border-radius: 12px;
      box-shadow: 5px 6px 11px -11px gray;
      overflow: hidden;

      .plungin-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;

        .plugin-icon {
          display: inline-block;
          width: 60px;
          height: 60px;
          border-radius: 50%;
          background-color: #e2edfd;
          color: #3a84f6;
          text-align: center;
          line-height: 60px;
          font-weight: 700;
          font-size: 26px;
        }

        .binddingText {
          color: #b0b2b4;
        }
      }

      .plugin-name {
        font-weight: 700;
        font-size: 15px;
        color: #2e2d32;
      }

      .binding {
        .binding-list {
          display: flex;
          justify-content: space-between;
          margin: 5px 0 9px;
          color: #b0b2b4;

          .binding-empty {
            color: #64666a;
            font-weight: 700;
          }

          .binding-number {
            color: #4482e4;
            font-weight: 700;
          }

        }
      }


      .plugin-notes {
        color: 808487;
      }

      .plugin-chose {
        position: absolute;
        width: 0;
        height: 0;
        border-top: 45px solid #3B83FC;
        border-left: 45px solid transparent;
        top: 0;
        right: 0;

        .choose-icon {
          position: absolute;
          width: 20px;
          height: 20px;
          line-height: 20px;
          text-align: center;
          top: -41px;
          right: 7px;
          font-size: 26px;
          color: #fff;
          border-radius: 50%;
        }
      }
    }

    .plugin:nth-child(3n) {
      margin-right: 0px;
    }

    .disabled::after {
      user-select: none;
      cursor: not-allowed;
      content: "";
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background-color: rgba(250, 252, 254, 0.5);
      z-index: 1;
      border-radius: 12px;
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
    height: calc(100vh - 106px) !important;
  }

  .slider-footer {
    display: flex;

    .fist-step {
      margin-right: 12px;
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
    left: 16px;
    top: 15px;
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

.form-key-cls{
  font-size: 12px;
  color: #63656E;
  padding: 5px 0;
}
.form-val-cls{
  font-size: 12px;
  color: #313238;
}
</style>
