<template>
  <div class="response-container">
    <bk-collapse
      class="bk-collapse-response"
      v-model="activeIndex"
      @update:model-value="handleCollapse"
    >
      <bk-collapse-panel :name="1">
        <template #header>
          <div class="response-title flex">
            <div :class="['response-type', 'flex', activeIndex?.includes(1) ? '' : 'fold-header']">
              <angle-up-fill :class="['header-icon', activeIndex?.includes(1) ? '' : 'fold']" />
              <span class="fold-title" v-show="!activeIndex?.includes(1)">{{ t('返回响应') }}</span>
              <bk-tab
                v-model:active="tabActive"
                type="unborder-card"
                class="response-type-tab"
                v-show="activeIndex?.includes(1)"
                @click="stopPropa">
                <bk-tab-panel label="Body" name="body"></bk-tab-panel>
                <bk-tab-panel :label="t('请求详情')" name="detail"></bk-tab-panel>
                <bk-tab-panel label="Headers" name="headers"></bk-tab-panel>
              </bk-tab>
            </div>
            <div class="response-status flex" @click="stopPropa" v-show="activeIndex?.includes(1)">
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
              <div class="response-content-type flex" v-show="tabActive === 'body'">
                <div class="payload-type">
                  <div
                    :class="['payload-type-item', bodyType === 'pretty' ? 'active' : '']"
                    @click="handleBodyTypeChange('pretty')"
                  >
                    <span class="icon apigateway-icon icon-ag-cardd"></span>
                    Pretty
                  </div>
                  <div
                    :class="['payload-type-item', bodyType === 'raw' ? 'active' : '']"
                    @click="handleBodyTypeChange('raw')"
                  >
                    <span class="icon apigateway-icon icon-ag-shitu-liebiao"></span>
                    Raw
                  </div>
                </div>
                <bk-select
                  class="bk-select"
                  v-model="responseType"
                  :clearable="false"
                  :filterable="false"
                  :disabled="true"
                  v-bk-tooltips="t('暂不支持切换')"
                >
                  <bk-option
                    v-for="(item, index) in bodyTypeList"
                    :id="item.value"
                    :key="index"
                    :name="item.label"
                  />
                </bk-select>
              </div>
              <div class="response-content-type flex" v-show="tabActive === 'detail'">
                <div class="payload-type">
                  <div class="payload-type-item active">
                    <span class="icon apigateway-icon icon-ag-shell"></span>
                    Shell
                  </div>
                <!-- <div class="payload-type-item">
                  <span class="icon apigateway-icon icon-ag-python"></span>
                  Python
                </div> -->
                </div>
                <bk-select
                  class="bk-select"
                  v-model="detailsType"
                  :clearable="false"
                  :filterable="false"
                  :disabled="true"
                  v-bk-tooltips="t('暂不支持切换')"
                >
                  <bk-option
                    v-for="(item, index) in detailsTypeList"
                    :id="item.value"
                    :key="index"
                    :name="item.label"
                  />
                </bk-select>
              </div>
              <div class="response-content">
                <editor-monaco
                  v-model="editorText"
                  theme="Visual Studio"
                  ref="resourceEditorRef"
                  language="json"
                  :minimap="false"
                  :show-copy="true"
                  :show-full-screen="true"
                  :read-only="true"
                />
              </div>
            </template>
            <template v-else>
              <bk-table
                class="table-layout"
                ref="bkTableRef"
                :data="tableData"
                show-overflow-tooltip
                row-hover="auto"
                :border="['outer', 'col']">
                <bk-table-column :label="t('名称')" prop="name"></bk-table-column>
                <bk-table-column :label="t('值')" prop="value"></bk-table-column>
              </bk-table>
            </template>
          </div>
        </template>
      </bk-collapse-panel>
    </bk-collapse>
  </div>
</template>

<script lang="ts" setup>
import { ref, watch, computed, nextTick } from 'vue';
import { AngleUpFill } from 'bkui-vue/lib/icon';
import { useI18n } from 'vue-i18n';
import editorMonaco from '@/components/ag-editor.vue';

const { t } = useI18n();

const props = defineProps({
  res: {
    type: Object,
    default: {},
  },
});

const emit = defineEmits(['response-fold', 'response-unfold']);

type TableDataItem = {
  name: String;
  value: String;
};

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
const resourceEditorRef: any = ref<InstanceType<typeof editorMonaco>>();
const data = ref<any>({});

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

const stopPropa = (e: Event) => {
  e?.stopPropagation();
};

const formatBody = () => {
  nextTick(() => {
    resourceEditorRef.value?.updateOptions({
      readOnly: false,
    });
    setTimeout(() => {
      resourceEditorRef.value?.handleFormat();
    });
    setTimeout(() => {
      resourceEditorRef.value?.updateOptions({
        readOnly: true,
      });
    }, 200);
  });
};

const handleBodyTypeChange = (type: string) => {
  bodyType.value = type;
  if (type === 'pretty') {
    formatBody();
  } else {
    setEditorValue();
  }
};

const setEditorValue = (fold?: boolean) => {
  if (tabActive.value === 'body') {
    editorText.value = data.value?.body || '';
  } else {
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
  } else {
    tableData.value = [];
  }
};

const handleCollapse = () => {
  if (!activeIndex.value?.includes(1)) {
    emit('response-fold');
  } else {
    emit('response-unfold');
  }
};

const setInit = () => {
  activeIndex.value = [];
  tabActive.value = 'body';
  bodyType.value = 'pretty';
  emit('response-fold');
};

watch(
  () => tabActive.value,
  (v) => {
    if (v !== 'headers') {
      setEditorValue();
    }
  },
);

watch(
  () => props.res,
  (v) => {
    data.value = v || {};
    tabActive.value = 'body';
    setEditorValue(JSON.stringify(v) === '{}');
    setTableData();
  },
);

defineExpose({
  setInit,
});

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
</style>
