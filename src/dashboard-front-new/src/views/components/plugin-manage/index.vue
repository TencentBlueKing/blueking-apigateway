<template>
  <div class="plugin-container">
    <!-- 默认展示 -->
    <bk-exception
      class="exception-wrap-item"
      type="empty"
      :class="{ 'exception-gray': false }"
    >
      {{ t("尚未添加插件，") }}
      <bk-button text theme="primary" @click="handlePluginAdd">
        {{ t("立即添加") }}
      </bk-button>
    </bk-exception>
    <!-- 添加插件 -->
    <bk-sideslider
      v-model:isShow="isVisible"
      :title="t('添加插件')"
      quick-close
      ext-cls="plugin-add-slider"
      width="960"
    >
      <template #default>
        <bk-steps
          :cur-step="state.curStep"
          :steps="state.plugintSteps"
          ext-cls="plugin-add-steps"
        />
        <div class="plugin-add-container">
          <div class="plugins pl20 pr20" v-if="state.curStep === 1">
            <div class="plugin-search">
              <bk-input
                v-model="searchValue"
                clearable
                type="search"
                :placeholder="t('请输入插件关键字')"
                @enter="handleSearch"
                @clear="handleClear"
              />
            </div>
            <div class="plugin-list">
              <div
                :class="[item.is_bound ? 'plugin disabled' : 'plugin ']"
                v-for="item in pluginListDate"
                :key="item.id"
                @click="handleChoosePlugin(item)"
              >
                <span class="plugin-icon">
                  {{ pluginCodeFirst(item.code) }}
                </span>
                <p class="plugin-name">{{ item.name }}</p>
                <div class="binding">
                  <ul class="binding-list">
                    <li>版本：<span>V1.0.0</span></li>
                    <li>
                      已绑环境：
                      <span :class="[item.related_scope_count.stage === 0 ? 'binding-empty' : 'binding-number',]">
                        {{ item.related_scope_count.stage }}
                      </span>
                    </li>
                    <li>
                      已绑资源：
                      <span
                        :class="[
                          item.related_scope_count.resource === 0
                            ? 'binding-empty'
                            : 'binding-number',
                        ]"
                      >
                        {{ item.related_scope_count.resource }}
                      </span>
                    </li>
                  </ul>
                </div>
                <div class="plugin-notes">
                  {{ item.notes }}
                </div>
              </div>
            </div>
          </div>
          <div class="plugin-config pl20 pt20 pr20" v-else>
            <pluginInfo :cur-plugin="curChoosePlugin"></pluginInfo>
          </div>
        </div>
      </template>
      <template #footer>
        <div class="slider-footer pl20">
          <div class="fist-step" v-if="state.curStep === 1">
            <bk-button theme="primary" @click="handelNext" width="50px">{{
              t("下一步")
            }}</bk-button>
          </div>
          <div class="last-step" v-else>
            <bk-button theme="primary" @click="handleAdd">{{
              t("确定")
            }}</bk-button>
            <bk-button @click="handlePre" class="pre-btn">{{
              t("上一步")
            }}</bk-button>
          </div>
          <bk-button @click="handleCancel">{{ t("取消") }}</bk-button>
        </div>
      </template>
    </bk-sideslider>
  </div>
</template>

<script setup lang="ts">
import pluginInfo from './plugin-info.vue';
import { ref, reactive, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useCommon, useStage } from '@/store';
import { useRoute } from 'vue-router';
import {
  getPluginListData,
  getPluginBindingsList,
  getPluginForm,
  getScopeBindingPluginList,
} from '@/http';

const props = defineProps({
  resourceId: {
    type: Number,
    default: 0,
  },
});

const { t } = useI18n();
const route = useRoute();
const common = useCommon();
const stage = useStage();

const { apigwId } = common; // 网关id
const { curStageId } = stage; // 当前stage_id

const isVisible = ref(false);
const searchValue = ref('');
const scopeType = ref('');
const scopeId = ref<number>(-1);
const pluginListDate = ref<any>({});
const curChoosePlugin = ref<any>({});
const state = reactive({
  plugintSteps: [
    { title: t('选择插件'), icon: 1 },
    { title: t('配置插件'), icon: 2 },
  ],
  curStep: 1,
});
onMounted(() => {
  console.log(curStageId);
});
const pluginCodeFirst = computed(() => (code: string) => {
  return code.charAt(3).toUpperCase();
});

// 获取可配置的插件列表
const getPluginListDetails = async (params: any) => {
  const res = await getPluginListData(apigwId, params);
  pluginListDate.value = res.results;
  console.log(pluginListDate.value);
};

// 立即添加
const handlePluginAdd = async () => {
  isVisible.value = true;
  state.curStep = 1;
  scopeType.value = route.path.includes('stage') ? 'stage' : 'resource';
  scopeId.value = route.path.includes('stage') ? curStageId : props.resourceId;
  const params = {
    scope_type: scopeType.value,
    scope_id: scopeId.value,
  };
  try {
    getPluginListDetails(params);
  } catch (error) {
    console.log('error', error);
  }
};
const handleChoosePlugin = (item: any) => {
  if (item.is_bound) {
    return;
  }
  curChoosePlugin.value = item;
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
  handlePluginAdd();
};
// 下一页
const handelNext = () => {
  state.curStep = 2;
};
// 上一页
const handlePre = () => {
  state.curStep = 1;
};
// 确认添加
const handleAdd = () => {
  // state.curStep = 1;
};
// 取消添加
const handleCancel = () => {
  // isVisible.value = true;
};
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
  height: calc(100vh - 170px) !important;
  border-top: 1px solid #e3e3e5;
}
.plugins {
  background-color: #f5f7fb;
  height: 100%;

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
      cursor: pointer;
      margin-right: 18px;
      margin-bottom: 20px;
      width: 32%;
      padding: 20px 20px;
      background-color: #fff;
      border-radius: 12px;
      box-shadow: 5px 6px 11px -11px gray;
      .plugin-icon {
        display: inline-block;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background-color: #e2edfd;
        color: #3a84f6;
        text-align: center;
        line-height: 60px;
        font-weight: 600;
        font-size: 26px;
        margin-bottom: 15px;
      }
      .plugin-name {
        font-weight: 900;
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
            font-weight: 600;
          }
          .binding-number {
            color: #4482e4;
            font-weight: 600;
          }
        }
      }
      .plugin-notes {
        color: #7f8182;
      }
    }
    .plugin:nth-child(3n) {
      margin-right: 0px;
    }
    .disabled{
      user-select: none;
      cursor: not-allowed;
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
    .last-step {
      .pre-btn {
        margin-left: 8px;
        margin-right: 12px;
      }
    }
  }
}
</style>
