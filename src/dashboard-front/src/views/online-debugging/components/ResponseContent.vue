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
  <div class="response-container">
    <BkCollapse
      v-model="activeIndex"
      class="bk-collapse-response"
      @update:model-value="handleCollapse"
    >
      <BkCollapsePanel :name="1">
        <template #header>
          <div class="response-title flex">
            <div
              class="response-type flex"
              :class="[activeIndex?.includes(1) ? '' : 'fold-header']"
            >
              <AngleUpFill
                class="header-icon"
                :class="[activeIndex?.includes(1) ? '' : 'fold']"
              />
              <span
                v-show="!activeIndex?.includes(1)"
                class="fold-title"
              >{{ t('返回响应') }}</span>
              <BkTab
                v-show="activeIndex?.includes(1)"
                v-model:active="tabActive"
                type="unborder-card"
                class="response-type-tab"
                @click="stopPropagation"
              >
                <BkTabPanel
                  label="Body"
                  name="body"
                />
                <BkTabPanel
                  :label="t('请求详情')"
                  name="detail"
                />
                <BkTabPanel
                  label="Headers"
                  name="headers"
                />
              </BkTab>
            </div>
            <div
              v-show="activeIndex?.includes(1)"
              class="response-status flex"
              @click="stopPropagation"
            >
              <div
                v-if="featureFlagStore.isAIEnabled"
                class="response-status-item"
              >
                <AiBluekingButton @click="handleAIClick" />
              </div>
              <div class="response-status-item">
                <span class="label">Status：</span>
                <span :class="statusColor">
                  {{ data?.status_code || '--' }}
                </span>
              </div>
              <div class="response-status-item">
                <span class="label">Time：</span>
                <span class="value">{{ data?.proxy_time || 0 }} ms</span>
              </div>
              <div class="response-status-item">
                <span class="label">Size：</span>
                <span class="value">{{ data?.size || 0 }} KB</span>
              </div>
            </div>
          </div>
        </template>
        <template #content>
          <div class="response-main">
            <template v-if="tabActive !== 'headers'">
              <div
                v-show="tabActive === 'body'"
                class="response-content-type flex"
              >
                <div class="payload-type">
                  <div
                    class="payload-type-item"
                    :class="[bodyType === 'pretty' ? 'active' : '']"
                    @click="() => handleBodyTypeChange('pretty')"
                  >
                    <span class="icon apigateway-icon icon-ag-cardd" />
                    Pretty
                  </div>
                  <div
                    class="payload-type-item"
                    :class="[bodyType === 'raw' ? 'active' : '']"
                    @click="() => handleBodyTypeChange('raw')"
                  >
                    <span class="icon apigateway-icon icon-ag-shitu-liebiao" />
                    Raw
                  </div>
                </div>
                <BkSelect
                  v-model="responseType"
                  v-bk-tooltips="t('暂不支持切换')"
                  class="bk-select"
                  :clearable="false"
                  :filterable="false"
                  disabled
                >
                  <BkOption
                    v-for="(item, index) in bodyTypeList"
                    :id="item.value"
                    :key="index"
                    :name="item.label"
                  />
                </BkSelect>
              </div>
              <div
                v-show="tabActive === 'detail'"
                class="response-content-type flex"
              >
                <div class="payload-type">
                  <div class="payload-type-item active">
                    <span class="icon apigateway-icon icon-ag-shell" />
                    Shell
                  </div>
                <!-- <div class="payload-type-item">
                  <span class="icon apigateway-icon icon-ag-python"></span>
                  Python
                  </div> -->
                </div>
                <BkSelect
                  v-model="detailsType"
                  v-bk-tooltips="t('暂不支持切换')"
                  class="bk-select"
                  :clearable="false"
                  :filterable="false"
                  disabled
                >
                  <BkOption
                    v-for="(item, index) in detailsTypeList"
                    :id="item.value"
                    :key="index"
                    :name="item.label"
                  />
                </BkSelect>
              </div>
              <div class="response-content">
                <EditorMonaco
                  ref="resourceEditorRef"
                  v-model="editorText"
                  theme="Visual Studio"
                  language="json"
                  :minimap="false"
                  show-copy
                  show-full-screen
                  read-only
                />
              </div>
            </template>
            <template v-else>
              <BkTable
                class="table-layout"
                :data="tableData"
                show-overflow-tooltip
                row-hover="auto"
                :border="['outer', 'col']"
              >
                <BkTableColumn
                  :label="t('名称')"
                  prop="name"
                />
                <BkTableColumn
                  :label="t('值')"
                  prop="value"
                />
              </BkTable>
            </template>
          </div>
        </template>
      </BkCollapsePanel>
    </BkCollapse>
    <AiChatSlider
      v-if="featureFlagStore.isAIEnabled"
      v-model="isAISliderShow"
      :message="aiRequestMessage"
      :title="t('状态分析')"
    />
  </div>
</template>

<script lang="ts" setup>
import { useFeatureFlag } from '@/stores';
import { AngleUpFill } from 'bkui-vue/lib/icon';
import EditorMonaco from '@/components/ag-editor/Index.vue';
import AiBluekingButton from '@/components/ai-seek/AiBluekingButton.vue';
import AiChatSlider from '@/components/ai-seek/AiChatSlider.vue';

type TableDataItem = {
  name: string
  value: string
};

interface IProps { res?: object }

const { res = {} } = defineProps<IProps>();

const emit = defineEmits<{
  ResponseFold: [data?: any ]
  ResponseUnfold: [data?: any ]
}>();

const { t } = useI18n();
const featureFlagStore = useFeatureFlag();

const activeIndex = ref<number[]>([]);
const tabActive = ref<string>('body');
const responseType = ref<string>('JSON');
const tableData = ref<TableDataItem[]>([]);
const bodyTypeList = ref([
  {
    value: 'JSON',
    label: 'JSON',
  },
  {
    value: 'XML',
    label: 'XML',
  },
  {
    value: 'HTML',
    label: 'HTML',
  },
  {
    value: 'TEXT',
    label: 'TEXT',
  },
]);
const bodyType = ref<string>('pretty');
const detailsType = ref<string>('cURL');
const detailsTypeList = ref([
  {
    value: 'cURL',
    label: 'cURL',
  },
]);
const editorText = ref<any>('');
const resourceEditorRef: any = ref<InstanceType<typeof EditorMonaco>>();
const data = ref<any>({});
const isAISliderShow = ref(false);
const aiRequestMessage = ref('');

const statusColor = computed(() => {
  let color = 'value';
  const code = String(data.value?.status_code);
  if (code?.startsWith('4')) {
    color = 'warning';
  }
  if (code?.startsWith('5')) {
    color = 'error';
  }

  return color;
});

watch(
  () => tabActive.value,
  (value) => {
    if (value !== 'headers') {
      setEditorValue();
    }
  },
);

watch(
  () => res,
  (value) => {
    data.value = value || {};
    tabActive.value = 'body';
    setEditorValue(JSON.stringify(value) === '{}');
    setTableData();
  },
);

const stopPropagation = (event: Event) => {
  event?.stopPropagation();
};

const formatBody = () => {
  nextTick(() => {
    resourceEditorRef.value?.updateOptions({ readOnly: false });
    setTimeout(() => {
      resourceEditorRef.value?.handleFormat();
    });
    setTimeout(() => {
      resourceEditorRef.value?.updateOptions({ readOnly: true });
    }, 200);
  });
};

const handleBodyTypeChange = (type: string) => {
  bodyType.value = type;
  if (type === 'pretty') {
    formatBody();
  }
  else {
    setEditorValue();
  }
};

const setEditorValue = (fold?: boolean) => {
  if (tabActive.value === 'body') {
    editorText.value = data.value?.body || '';
  }
  else {
    editorText.value = data.value?.curl || '';
  }
  resourceEditorRef.value?.setValue(editorText.value);
  if (tabActive.value === 'body' && bodyType.value === 'pretty') {
    formatBody();
  }

  if (fold) {
    activeIndex.value = [];
    return;
  }
  activeIndex.value = [1];
};

const setTableData = () => {
  const { headers } = data.value;
  if (headers && JSON.stringify(headers) !== '{}') {
    const list: TableDataItem[] = [];
    Object.keys(headers).forEach((key: string) => {
      list.push({
        name: key,
        value: headers[key],
      });
    });

    tableData.value = list;
  }
  else {
    tableData.value = [];
  }
};

const handleCollapse = () => {
  if (!activeIndex.value?.includes(1)) {
    emit('ResponseFold');
  }
  else {
    emit('ResponseUnfold');
  }
};

const setInit = () => {
  activeIndex.value = [];
  tabActive.value = 'body';
  bodyType.value = 'pretty';
  emit('ResponseFold');
};

const handleAIClick = () => {
  try {
    aiRequestMessage.value = JSON.stringify(res, null, 2);
    isAISliderShow.value = true;
  }
  catch {
    aiRequestMessage.value = '';
  }
};

defineExpose({ setInit });

</script>

<style lang="scss" scoped>
.response-container {
  padding-left: 24px;
  height: 100%;
  .response-title {
    position: relative;
    .response-type {
      flex: 1;
      cursor: pointer;
      transition: all .2s;
      &.fold-header {
        display: flex;
        align-items: center;
        line-height: 52px;
        .header-icon {
          margin-top: 0px;
        }
      }
      .header-icon {
        margin-top: -18px;
        margin-right: 8px;
        transition: all .2s;
        cursor: pointer;
        &.fold {
          transform: rotate(-90deg);
        }
      }
      .response-type-tab {
        flex: 1;
      }
      .fold-title {
        font-weight: 700;
        font-size: 14px;
        color: #313238;
      }
    }
    .response-status {
      position: absolute;
      top: 18px;
      right: 24px;
      .response-status-item {
        font-size: 12px;
        margin-left: 12px;
        .label {
          color: #63656E;
        }
        .value {
          color: #1CAB88;
        }
        .warning {
          color: #FF9C01;
        }
        .error {
          color: #EA3636;
        }
      }
    }
  }
  .response-main {
    padding-bottom: 15px;
    height: 100%;
    overflow-y: auto;
    box-sizing: border-box;
    .response-content-type {
      margin-bottom: 12px;
      .payload-type {
        margin-right: 8px;
      }
    }
    .response-content {
      height: calc(100% - 44px);
      overflow: hidden;
      background: #FFFFFF;
      border: 1px solid #DCDEE5;
      border-radius: 2px;
    }
  }
  .bk-collapse-response {
    height: 100%;
    :deep(.bk-collapse-item) {
      height: 100%;
    }
    :deep(.bk-collapse-content) {
      padding: 0;
      height: calc(100% - 72px);
    }
  }
}
.flex {
  display: flex;
  align-items: center;
}
.payload-type {
  display: flex;
  align-items: center;
  background: #F0F1F5;
  border-radius: 2px;
  padding: 4px;
  .payload-type-item {
    display: flex;
    align-items: center;
    font-size: 12px;
    color: #63656E;
    padding: 1px 10px;
    cursor: pointer;
    .apigateway-icon {
      margin-right: 4px;
      font-size: 16px;
    }
    &.active  {
      color: #3A84FF;
      background-color: #fff;
      border-radius: 2px;
    }
  }
}

.table-layout {
  :deep(.bk-scrollbar .bk__rail-x) {
    display: none;
    opacity: 0
  }
}
</style>
