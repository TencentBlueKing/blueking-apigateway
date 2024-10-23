<template>
  <div ref="searchInputRef" class="search-input-container">
    <bk-popover
      :is-show="searchUsage.showed"
      trigger="click"
      width="506"
      theme="light"
      placement="bottom"
      ext-cls="access-log-popover"
      @after-show="handlePopoverShow"
      @after-hidden="handlePopoverHidden">
      <div class="statement-example">
        <span class="icon apigateway-icon icon-ag-help-document"></span>
        <span class="example-text">{{ t('如何使用') }}</span>
      </div>
      <template #content>
        <div class="access-log-search-usage-content">
          <div class="sample">
            <div class="sample-item">
              <p class="mode">{{ t("关键字搜索") }}</p>
              <p class="value">
                request_id: b3e2497532e54f518b3d1267fb67c83a
                <span
                  class="icon apigateway-icon icon-ag-3-yuan-bohui"
                  @click="handleClickUsageValue('request_id: b3e2497532e54f518b3d1267fb67c83a')"
                  v-bk-tooltips="{ content: '引用条件' }">
                </span>
              </p>
            </div>
            <div class="sample-item">
              <p class="mode">{{ t("多个关键字匹配，支持 OR , AND") }}</p>
              <p class="value">
                (app_code: "app-template" AND client_ip: "1.0.0.1") OR resource_name: get_user
                <span
                  class="icon apigateway-icon icon-ag-3-yuan-bohui"
                  @click="handleClickUsageValue('')"
                  v-bk-tooltips="{ content: '引用条件' }">
                </span>
              </p>
            </div>
            <div class="sample-item">
              <p class="mode">{{ t("排除关键字") }}</p>
              <p class="value">
                -status: 200
                <span
                  class="icon apigateway-icon icon-ag-3-yuan-bohui"
                  @click="handleClickUsageValue('-status: 200')"
                  v-bk-tooltips="{ content: '引用条件' }">
                </span>
              </p>
            </div>
            <div class="sample-item">
              <p class="mode">{{ t("配置范围") }}</p>
              <p class="value">
                request_duration: [5000 TO 30000]
                <span
                  class="icon apigateway-icon icon-ag-3-yuan-bohui"
                  @click="handleClickUsageValue('request_duration: [5000 TO 30000]')"
                  v-bk-tooltips="{ content: '引用条件' }">
                </span>
              </p>
            </div>
          </div>
          <div class="more">
            {{ t("更多示例请参阅") }}
            <a class="link" target="_blank" :href="GLOBAL_CONFIG.DOC.QUERY_USE">
              {{ t("“请求流水查询规则”") }}
            </a>
          </div>
        </div>
      </template>
    </bk-popover>
    <bk-dropdown :popover-options="popoverOptions" :disabled="queryHistory.length === 0" style="width: 100%;">
      <bk-input
        class="search-input"
        v-model="localValue"
        :placeholder="localPlaceholder"
        clearable
        @enter="handleEnter"
      >
        <!-- <template #suffix>
          <bk-button theme="primary" class="search-input-button" @click="handleSearch"> {{ t("搜索") }} </bk-button>
        </template> -->
      </bk-input>
      <template #content>
        <bk-dropdown-menu>
          <bk-dropdown-item
            v-for="item in queryHistory"
            :key="item"
            @click="handleHistoryClick(item)"
          >
            {{ item }}
          </bk-dropdown-item>
        </bk-dropdown-menu>
      </template>
    </bk-dropdown>
  </div>
</template>

<script lang="ts" setup>
import {
  ref,
  watch,
} from 'vue';
import i18n from '@/language/i18n';
import { useGetGlobalProperties } from '@/hooks';
import { useStorage } from '@vueuse/core';
const { t } = i18n.global;

const globalProperties = useGetGlobalProperties();
// 从本地存储获取搜索历史
const queryHistory = useStorage('access-log-query-history', []);
const { GLOBAL_CONFIG } = globalProperties;

const props = defineProps({
  modeValue: {
    type: String,
    default: '',
  },
  placeholder: {
    type: String,
    default: '',
  },
  width: {
    type: String,
    default: '612px',
  },
});

const emit = defineEmits(['update:modeValue', 'search', 'choose']);

const popoverOptions = {
  trigger: 'click',
  placement: 'bottom-start',
};

const searchInputRef = ref(null);
const localValue = ref('');
const localPlaceholder = ref('');
localPlaceholder.value = props.placeholder || t('请输入查询语句');
const searchUsage = ref({
  showed: false,
});

watch(
  () => props.modeValue,
  (payload: string) => {
    localValue.value = payload;
  },
);

watch(
  () => localValue.value,
  (payload: string) => {
    emit('update:modeValue', payload);
  },
);

const handlePopoverShow = ({ isShow }: Record<string, boolean>) => {
  searchUsage.value.showed = isShow;
};

const handlePopoverHidden = ({ isShow }: Record<string, boolean>) => {
  searchUsage.value.showed = isShow;
};

const handleClickUsageValue = (innerText: string) => {
  if (!innerText) {
    innerText = '(app_code: "app-template" AND client_ip: "1.0.0.1") OR resource_name: get_user';
  }
  emit('choose', innerText);
};

const handleEnter = () => {
  emit('search', localValue.value);
};

const handleHistoryClick = (item: string) => {
  localValue.value = item;
};

defineExpose({
  searchInputRef: searchInputRef.value,
});
</script>

<style lang="scss" scoped>
.search-input {
  .search-input-button {
    height: auto;
    border: none;
    border-radius: 0;
  }
}
.search-input-container {
  position: relative;
  .statement-example {
    position: absolute;
    right: 0;
    top: -38px;
    display: flex;
    align-items: center;
    color: #3A84FF;
    font-size: 16px;
    cursor: pointer;
    .example-text {
      margin-left: 4px;
      font-size: 12px;
    }
  }
}

.access-log-search-usage-content {
  padding: 8px 4px -2px;
  .sample {
    border-bottom: 1px solid #DCDEE5;
    margin-bottom: 8px;
    padding-bottom: 12px;
    .sample-item:not(:nth-last-child(1)) {
      margin-bottom: 16px;
    }
    .mode {
      font-weight: bold;
      font-size: 12px;
      color: #63656E;
      margin-bottom: 4px;
      font-family: MicrosoftYaHei-Bold;
    }
    .value {
      font-size: 12px;
      color: #63656E;
      span {
        color: #3A84FF;
        cursor: pointer;
        margin-left: 2px;
        font-size: 14px;
      }
    }
  }
  .more {
    font-size: 12px;
    color: #63656e;
    .link {
      color: #3a84ff;
      cursor: pointer;
    }
  }
}
</style>
