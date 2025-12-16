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
  <div class="guide-line-content">
    <!-- 是否需要展示自定义使用指引tab -->
    <template v-if="showUsageGuide">
      <BkAlert
        v-if="!isExistCustomGuide"
        theme="info"
        class="mt-24px"
      >
        <template #title>
          <div class="flex">
            <div class="color-#4d4f56">
              {{ t('平台提供默认使用指引，您可添加自定义内容来补充说明。') }}
            </div>
            <BkButton
              text
              theme="primary"
              class="ml-8px"
              @click="handleShowGuide('add')"
            >
              {{ t('添加自定义使用指引') }}
            </BkButton>
          </div>
        </template>
      </BkAlert>
      <div
        v-else
        class="flex items-center flex-nowrap p-t-24px usage-guide-list"
      >
        <div
          v-for="item of USAGE_GUIDE_LIST"
          :key="item.value"
          class="usage-guide-item"
          :class="[
            {
              'is-active': item.value === activeTab,
            },
          ]"
          @click.stop="handleTabChange(item.value)"
        >
          <div class="flex items-center">
            <div>{{ item.label }}</div>
            <template v-if="['custom'].includes(item.value)">
              <AgIcon
                name="edit-small"
                size="26"
                class="edit-action hidden!"
                @click.stop="handleShowGuide('edit')"
              />
              <Close
                class="color-#EA3636 text-16px hidden! delete-icon"
                @click.stop="handleDeleteGuide"
              />
            </template>
          </div>
        </div>
      </div>
    </template>

    <Guide :markdown-html="markdownHtml" />

    <CustomMdGuideSlider
      v-model:is-show="isShowGuideSlider"
      :gateway-id="gatewayId"
      :markdown-text="markdownText"
      :guide-type="guideType"
      @confirm="handleGuideConfirm"
    />
  </div>
</template>

<script lang="ts" setup>
import { Message } from 'bkui-vue';
import { Close } from 'bkui-vue/lib/icon';
import { USAGE_GUIDE_LIST } from '@/constants';
import { usePopInfoBox } from '@/hooks';
import {
  deleteCustomServerGuideDoc,
  getCustomServerGuideDoc,
} from '@/services/source/mcp-server';
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';
import Guide from '@/components/guide/Index.vue';
import CustomMdGuideSlider from '@/views/mcp-market/components/CustomMdGuideSlider.vue';

interface IProps {
  markdownStr?: string
  gatewayId?: number
  showUsageGuide?: boolean
}

const isExistCustomGuide = defineModel('isExistCustomGuide', {
  type: Boolean,
  default: false,
});

const {
  markdownStr = '',
  gatewayId = 0,
  showUsageGuide = false,
} = defineProps<IProps>();

const emit = defineEmits<{ 'guide-change': [tabName: string] }>();

const { t } = useI18n();
const route = useRoute();

const md = new MarkdownIt({
  linkify: false,
  html: true,
  breaks: true,
  highlight(str: string, lang: string) {
    try {
      if (lang && hljs.getLanguage(lang)) {
        return hljs.highlight(str, {
          language: lang,
          ignoreIllegals: true,
        }).value;
      }
    }
    catch {
      return str;
    }
    return hljs.highlightAuto(str).value;
  },
});

const markdownText = ref('');
const markdownHtml = ref('');
const guideType = ref('');
const activeTab = ref('default');
const isShowGuideSlider = ref(false);

const serverId = computed(() => route.params.serverId);

watch(
  () => markdownStr,
  (newVal: string) => {
    markdownText.value = newVal;
    if (newVal) {
      markdownHtml.value = md.render(newVal);
    }
    else {
      markdownHtml.value = '';
    }
  },
  { immediate: true },
);

const fetchCustomGuide = async () => {
  const res = await getCustomServerGuideDoc(gatewayId, serverId.value);
  markdownText.value = res?.content ?? '';
  isExistCustomGuide.value = res?.content?.length > 0;
};

const handleTabChange = (tabName: string) => {
  activeTab.value = tabName;
  emit('guide-change', tabName);
};

const handleShowGuide = (mode: string) => {
  guideType.value = mode;
  const modeMap = {
    add: () => {
      return markdownText.value;
    },
    edit: () => {
      fetchCustomGuide();
    },
  };
  modeMap[mode]?.();
  isShowGuideSlider.value = true;
};

const handleDeleteGuide = () => {
  usePopInfoBox({
    isShow: true,
    type: 'warning',
    title: t('确认删除自定义使用指引？'),
    subTitle: t('删除后，MCP 文档中将显示默认指引'),
    confirmText: t('删除'),
    cancelText: t('取消'),
    confirmButtonTheme: 'danger',
    onConfirm: async () => {
      await deleteCustomServerGuideDoc(gatewayId, serverId.value);
      Message({
        message: t('删除成功'),
        theme: 'success',
      });
      guideType.value = '';
      isExistCustomGuide.value = false;
      handleTabChange('default');
    },
  });
};

const handleGuideConfirm = () => {
  handleTabChange('custom');
};
</script>

<style lang="scss" scoped>
.guide-line-content {
  padding: 0 24px 40px 48px;
  background-color: #ffffff;

  .usage-guide-list {
    box-sizing: border-box;

    .usage-guide-item {
      position: relative;
      color: #4d4f56;
      font-size: 14px;
      padding: 0 16px;
      border: 1px solid #dcdee5;
      border-right: 0;
      border-radius: 0 2px 2px 0;
      text-align: center;
      line-height: 32px;
      cursor: pointer;

      &:first-child {
        min-width: 116px;
      }

      &:last-child {
        border-right: 1px solid #dcdee5;

        &:hover {
          .edit-action,
          .delete-icon {
            display: block !important;

          }
        }
      }

      .delete-icon {
        position: absolute;
        top: -8px;
        right: -8px;
        background-color: #ffffff;
        border-radius: 50%;
      }

      &.is-active {
        background-color: #e1ecff;
        border-color: #3a84ff;
        color: #3a84ff;
        border-radius: 2px 0 0 2px;

        &.is-active + .usage-guide-item {
          border-left: 1px solid #3a84ff;
        }
      }
    }
  }
}

:deep(.ag-markdown-view) {
  .pre-wrapper {
    .ag-copy-btn {
      background-color: transparent;
    }
  }
}
</style>
