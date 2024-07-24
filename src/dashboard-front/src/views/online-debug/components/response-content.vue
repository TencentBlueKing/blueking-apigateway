<template>
  <div class="response-container">
    <bk-collapse
      class="bk-collapse-response"
      v-model="activeIndex"
    >
      <bk-collapse-panel :name="1">
        <template #header>
          <div class="response-title flex">
            <div class="response-type flex">
              <angle-up-fill :class="['header-icon', activeIndex?.includes(1) ? '' : 'fold']" />
              <bk-tab v-model:active="tabActive" type="unborder-card" class="response-type-tab" @click="stopPropa">
                <bk-tab-panel label="Body" name="body"></bk-tab-panel>
                <bk-tab-panel :label="t('请求详情')" name="detail"></bk-tab-panel>
              </bk-tab>
            </div>
            <div class="response-status flex" @click="stopPropa">
              <div class="response-status-item">
                <span class="label">Status：</span>
                <span class="value">{{ data?.status_code || '--' }}</span>
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
            <div class="response-content-type flex" v-show="tabActive === 'body'">
              <div class="payload-type">
                <div class="payload-type-item">
                  <span class="icon apigateway-icon icon-ag-menu"></span>
                  Pretty
                </div>
                <div class="payload-type-item active">
                  <span class="icon apigateway-icon icon-ag-menu"></span>
                  Raw
                </div>
              </div>
              <bk-select
                class="bk-select"
                v-model="responseType"
                :clearable="false"
                :filterable="false"
                :disabled="true"
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
                  <span class="icon apigateway-icon icon-ag-menu"></span>
                  Shell
                </div>
                <div class="payload-type-item">
                  <span class="icon apigateway-icon icon-ag-menu"></span>
                  Python
                </div>
              </div>
              <bk-select
                class="bk-select"
                v-model="detailsType"
                :clearable="false"
                :filterable="false"
                :disabled="true"
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
              <editor-monaco v-model="editorText" theme="Visual Studio" ref="resourceEditorRef" />
            </div>
          </div>
        </template>
      </bk-collapse-panel>
    </bk-collapse>
  </div>
</template>

<script lang="ts" setup>
import { ref, watch } from 'vue';
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

const activeIndex = ref<number[]>([1]);
const tabActive = ref<string>('body');
const responseType = ref<string>('JSON');
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

const stopPropa = (e: Event) => {
  e?.stopPropagation();
};

const setEditorValue = () => {
  if (tabActive.value === 'body') {
    editorText.value = data.value?.body || '';
  } else {
    editorText.value = data.value?.curl || '';
  }
  resourceEditorRef.value?.setValue(editorText.value);
};

watch(
  () => tabActive.value,
  () => {
    setEditorValue();
  },
);

watch(
  () => props.res,
  (v) => {
    data.value = v || {};
    tabActive.value = 'body';
    setEditorValue();
  },
);

</script>

<style lang="scss" scoped>
.response-container {
  padding-left: 24px;
  .response-title {
    position: relative;
    .response-type {
      flex: 1;
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
      }
    }
  }
  .response-main {
    padding-bottom: 15px;
    .response-content-type {
      margin-bottom: 12px;
      .payload-type {
        margin-right: 8px;
      }
    }
    .response-content {
      width: 100%;
      height: 235px;
      background: #FFFFFF;
      border: 1px solid #DCDEE5;
      border-radius: 2px;
    }
  }
  .bk-collapse-response {
    :deep(.bk-collapse-content) {
      padding: 0;
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
    padding: 4px 10px;
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
