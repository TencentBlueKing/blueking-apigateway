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
  <div class="res-doc-container">
    <BkSideslider
      v-model:is-show="isShow"
      quick-close
      :title="resource.name"
      width="780"
      v-bind="$attrs"
      @shown="handleShown"
      @hidden="handleHidden"
    >
      <template #default>
        <BkLoading :loading="isLoading || isTranslating">
          <main class="main-wrap">
            <div
              class="ag-markdown-view"
              :class="isEdited ? '' : 'text-center'"
            >
              <h3 v-if="isEdited">
                {{ t('文档类型') }}
              </h3>
              <template v-if="isEdited">
                <p class="pb-15px">
                  {{ language === 'zh' ? t('中文文档') : t('英文文档') }}
                </p>
              </template>
              <div
                v-else
                class="relative"
              >
                <BkButtonGroup>
                  <BkButton
                    v-for="item in languagesData"
                    :key="item.value"
                    :selected="language === item.value"
                    :disabled="isEdited && language !== item.value"
                    @click="() => handleSelectLanguage(item.value as 'zh' | 'en')"
                  >
                    <div>
                      {{ item.label }}
                    </div>
                  </BkButton>
                </BkButtonGroup>
                <template v-if="featureFlagStore.isAIEnabled">
                  <div
                    v-if="hasDoc"
                    v-bk-tooltips="{
                      content: isTranslating ? t('翻译中') : t('请先创建文档'),
                      disabled: !isTranslating && hasDocByLanguage(language),
                    }"
                    class="absolute right-0 top-7px flex items-center cursor-pointer"
                    @click="handleTranslateClick"
                  >
                    <AiBluekingButton
                      :disabled="isTranslating || !hasDocByLanguage(language)"
                      :tooltip-options="{ disabled: true }"
                    />
                    <div
                      class="text-12px"
                      :class="{
                        'color-#dcdee5 cursor-not-allowed': isTranslating || !hasDocByLanguage(language),
                        'gradient-text-color': !isTranslating && hasDocByLanguage(language),
                      }"
                    >
                      {{ language === 'zh' ? t('一键翻译英文') : t('一键翻译中文') }}
                    </div>
                  </div>
                </template>
              </div>
            </div>
            <div v-show="isEmpty">
              <div class="text-center mt-50px">
                <BkException
                  class="exception-wrap-item exception-part"
                  type="empty"
                  scene="part"
                  :description="language === 'zh' ? t('您尚未创建中文文档') : t('您尚未创建英文文档')"
                />
                <BkButton
                  v-if="showCreateBtn"
                  class="mt-20px w-120px"
                  theme="primary"
                  @click="() => handleEditMarkdown('create')"
                >
                  {{ t('立即创建') }}
                </BkButton>
              </div>
            </div>
            <div v-show="!isEmpty">
              <div class="ag-markdown-view">
                <h3> {{ language === 'zh' ? t('请求方法/请求路径') : 'Method/Path' }} </h3>
                <p class="pb-15px">
                  <span
                    class="ag-tag"
                    :class="resource.method.toLowerCase()"
                  >{{ resource.method }}</span>
                  {{ resource.path }}
                </p>
              </div>
              <div
                v-show="!isEdited"
                id="resource-doc-markdown"
                v-bk-xss-html="markdownHtml"
                class="ag-markdown-view"
              />
              <div
                v-show="isEdited"
                class="ag-markdown-editor"
              >
                <mavon-editor
                  ref="markdownRef"
                  v-model="markdownDoc"
                  :class="{ 'content-editor': !isFullscreen }"
                  :language="language"
                  :box-shadow="false"
                  :subfield="false"
                  :is-hljs="hljs"
                  :tab-size="4"
                  :toolbars="toolbars"
                  @full-screen="handleFullscreen"
                />
              </div>
            </div>
          </main>
        </BkLoading>
      </template>
      <!--  底部按钮  -->
      <template
        v-if="showFooter && !isLoading && !isEmpty"
        #footer
      >
        <div>
          <template v-if="isEdited">
            <BkButton
              class="mr-8px min-w-88px"
              theme="primary"
              :loading="isSaving"
              @click="handleSaveMarkdown"
            >
              {{ isUpdate ? t('更新') : t('提交') }}
            </BkButton>
            <BkButton
              class="min-w-88px"
              @click="handleCancelMarkdown"
            >
              {{ t('取消') }}
            </BkButton>
          </template>
          <template v-else>
            <BkButton
              class="mr-8px min-w-88px"
              theme="primary"
              @click="() => handleEditMarkdown('edit')"
            >
              {{ t('修改') }}
            </BkButton>
            <BkPopConfirm
              :title="t('确认要删除该文档？')"
              :content="t('将删除相关配置，不可恢复，请确认是否删除')"
              width="288"
              trigger="click"
              @confirm="handleDeleteMarkdown"
            >
              <BkButton class="min-w-88px">
                {{ t('删除') }}
              </BkButton>
            </BkPopConfirm>
          </template>
        </div>
      </template>
    </BkSideslider>
  </div>
</template>

<script setup lang="ts">
import MarkdownIt from 'markdown-it';
import { cloneDeep } from 'lodash-es';
import {
  deleteResourceDocs,
  getResourceDocPreview,
  getResourceDocs,
  saveResourceDocs,
  updateResourceDocs,
} from '@/services/source/resource.ts';
import {
  InfoBox,
  Message,
} from 'bkui-vue';
// import mitt from '@/common/event-bus';
import { copy } from '@/utils';
import { useRouteParams } from '@vueuse/router';
import AiBluekingButton from '@/components/ai-seek/AiBluekingButton.vue';
import { getAICompletion } from '@/services/source/ai.ts';
import hljs from 'highlight.js';
import { useFeatureFlag } from '@/stores';

interface IProps {
  resource?: object
  showFooter?: boolean
  showCreateBtn?: boolean
  isPreview?: boolean
  previewLang?: string | null
}

const isShow = defineModel<boolean>({
  required: true,
  default: false,
});

const {
  resource = {},
  showFooter = true,
  showCreateBtn = true,
  isPreview = false,
  previewLang = null,
} = defineProps<IProps>();

const emit = defineEmits<{
  'fetch': [void]
  'on-update': [type: string, isUpdate?: boolean]
}>();

const { t } = useI18n();
const featureFlagStore = useFeatureFlag();
const gatewayId = useRouteParams('id', 0, { transform: Number });

const languagesData = ref([{
  label: t('中文文档'),
  value: 'zh',
},
{
  label: t('英文文档'),
  value: 'en',
}]);
const isEmpty = ref(false);
const isUpdate = ref(false);
const markdownDoc = ref('');
const markdownHtml = ref('');
const docData = ref<any[]>([]);
const isEdited = ref(false); // 是否是编辑
const language = ref<'zh' | 'en'>('zh');
const isSaving = ref(false);
const isLoading = ref(true);
const docId = ref<any>('');
const markdownRef = ref(null);
const toolbars = ref<any>({
  bold: true,
  italic: true,
  header: true,
  underline: true,
  strikethrough: false,
  mark: true,
  superscript: false,
  subscript: false,
  quote: true,
  ol: true,
  ul: true,
  link: true,
  imagelink: false,
  code: true,
  table: true,
  fullscreen: true,
  readmodel: true,
  htmlcode: false,
  help: false,
  /* 1.3.5 */
  undo: false,
  redo: false,
  trash: false,
  save: false,
  /* 1.4.2 */
  navigation: false,
  /* 2.1.8 */
  alignleft: true,
  aligncenter: true,
  alignright: true,
  /* 2.2.1 */
  subfield: true,
  preview: true,
});
const isTranslating = ref(false);

const hasDoc = computed(() => {
  const cnDoc = docData.value.find((e: any) => e.language === 'zh')?.id;
  const enDoc = docData.value.find((e: any) => e.language === 'en')?.id;
  return cnDoc || enDoc;
});

const hasDocByLanguage = (lang: string) => !!docData.value.find((e: any) => e.language === lang)?.id;

// 渲染highlight的markdown
const renderHljsMd = (content: string) => {
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
      return str;
    },
  });
  markdownHtml.value = md.render(content);
};

// 编辑markdown
const handleEditMarkdown = (type: string) => {
  isEmpty.value = false;
  isEdited.value = true;

  isUpdate.value = type === 'edit'; // 是否是更新
  emit('on-update', 'update', isUpdate.value);
  const docDataItem = cloneDeep(docData.value)
    .find((e: any) => e.language === language.value);
  markdownDoc.value = docDataItem.content;
};

const isFullscreen = ref(false);
const handleFullscreen = (full: boolean) => {
  isFullscreen.value = full;
};

// 获取文档信息
const initData = async () => {
  isLoading.value = true;
  if (!isPreview) {
    docData.value = await getResourceDocs(gatewayId.value, resource.id);
  }
  else {
    // 预览资源文档会走到这里
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { backend, doc, _localId, _unchecked, ...restOfCurResource } = resource;

    const params = {
      review_resource: {
        ...restOfCurResource,
        backend_name: backend.name,
        backend_config: { ...backend.config },
      },
      doc_language: previewLang ?? language.value,
    };

    const res = await getResourceDocPreview(gatewayId.value, params);

    docData.value.push({
      id: null,
      language: previewLang ?? language.value,
      content: res.doc,
    });
  }
  // 根据语言找到是否有文档内容
  handleDocDataWithLanguage();
  isLoading.value = false;
};

const isDocEmptyByLanguage = (lang: string) => !docData.value.find((item: any) => item.language === lang)?.id;

const handleTranslateClick = async () => {
  if (isTranslating.value || !hasDocByLanguage(language.value)) {
    return;
  }
  // 要翻译成什么语言
  const targetLanguage = language.value === 'zh' ? 'en' : 'zh';
  const input = docData.value.find((item: any) => item.language === language.value)?.content;
  if (input) {
    // 判断目标语言的文档是否已存在，决定是调用创建文档接口还是更新文档接口
    if (isDocEmptyByLanguage(targetLanguage)) {
      Message({
        theme: 'primary',
        message: t('获取翻译中'),
      });
      isTranslating.value = true;
      const response = await getAICompletion(gatewayId.value, {
        inputs: {
          input,
          type: 'doc_translate',
          enable_streaming: false,
          language: targetLanguage,
        },
      });
      await saveResourceDocs(gatewayId.value, resource.id, {
        language: targetLanguage,
        content: response.content,
      });
      Message({
        theme: 'success',
        message: t('{lang}文档创建成功', { lang: targetLanguage === 'zh' ? t('中文') : t('英文') }),
      });
      initData();
      emit('fetch');
      isTranslating.value = false;
    }
    else {
      InfoBox({
        title: t('文档已存在，确定更新吗？'),
        infoType: 'warning',
        confirmText: t('更新'),
        cancelText: t('取消'),
        onConfirm: async () => {
          isTranslating.value = true;
          const response = await getAICompletion(gatewayId.value, {
            inputs: {
              input,
              type: 'doc_translate',
              enable_streaming: false,
              language: targetLanguage,
            },
          });
          const docId = docData.value.find((item: any) => item.language === targetLanguage)!.id;
          await updateResourceDocs(gatewayId.value, resource.id, {
            language: targetLanguage,
            content: response.content,
          }, docId);
          Message({
            theme: 'success',
            message: t('{lang}文档更新成功', { lang: language.value === 'zh' ? t('英文') : t('中文') }),
          });
          initData();
          emit('fetch');
          isTranslating.value = false;
        },
      });
    }
  }
};

// 保存markdown
const handleSaveMarkdown = async () => {
  if (!markdownDoc.value) {
    Message({
      theme: 'error',
      message: t('请输入文档内容'),
    });
    return false;
  }
  try {
    const data = {
      language: language.value,
      content: markdownDoc.value,
    };
    isSaving.value = true;
    if (docId.value) {
      // 更新
      await updateResourceDocs(gatewayId.value, resource.id, data, docId.value);
    }
    else {
      // 新增
      await saveResourceDocs(gatewayId.value, resource.id, data);
    }
    isEdited.value = false;
    Message({
      theme: 'success',
      message: t('保存成功！'),
    });
    initData();
    // 执行列表的方法
    emit('fetch');
  }
  finally {
    isSaving.value = false;
  }
};

const handleCancelMarkdown = () => {
  isEdited.value = false;
  emit('on-update', 'cancel');
};

// 删除文档
const handleDeleteMarkdown = async () => {
  await deleteResourceDocs(gatewayId.value, resource.id, docId.value);
  Message({
    message: t('删除成功'),
    theme: 'success',
  });
  initData();
  // 执行列表的方法
  emit('fetch');
};

const handleSelectLanguage = (payload: 'zh' | 'en') => {
  // 如果相同 则return
  if (payload === language.value) return;
  language.value = payload;
  handleDocDataWithLanguage();
};

// 根据语言找到是否有文档内容
const handleDocDataWithLanguage = () => {
  if (!isPreview) {
    const docDataItem = cloneDeep(docData.value)
      .find((e: any) => e.language === language.value);
    docId.value = docDataItem.id;
    isEmpty.value = !docDataItem.id;
    markdownDoc.value = docDataItem.content;
    renderHljsMd(docDataItem.content);
    nextTick(() => {
      const markdownDom = document.getElementById('resource-doc-markdown');
      if (markdownDom) {
        markdownDom.querySelectorAll('pre')?.forEach((preEl) => {
          const parentDiv = document.createElement('div');
          const codeBox = document.createElement('div');
          const btn = document.createElement('button');
          const code = preEl.querySelector('code')?.innerText || '';
          parentDiv.className = 'pre-wrapper';
          btn.className = 'ag-copy-btn';
          codeBox.className = 'code-box';
          btn.innerHTML = '<span title="复制"><i class="apigateway-icon icon-ag-copy-info"></i></span>';
          btn.setAttribute('data-copy', code);
          parentDiv.appendChild(btn);
          codeBox.appendChild(preEl.querySelector('code'));
          preEl.appendChild(codeBox);
          preEl.parentNode?.replaceChild(parentDiv, preEl);
          parentDiv.appendChild(preEl);
        });

        setTimeout(() => {
          const copyBtnEls = Array.from(document.getElementsByClassName('ag-copy-btn'));

          const handleCopy = function (this: any) {
            copy(this.dataset?.copy);
          };

          copyBtnEls.forEach((dom: any) => {
            dom.onclick = handleCopy;
          });
        }, 500);
      }
    });
  }
  else {
    // 预览资源文档会走到这里
    const doc = docData.value.find((d: any) => d.language === language.value);
    const content = doc?.content ?? '';
    markdownDoc.value = content;
    renderHljsMd(content);
  }
};

const escHandler = (e: KeyboardEvent) => {
  if (e.code === 'Escape') {
    if (markdownRef.value?.s_fullScreen) {
      markdownRef.value.s_fullScreen = false;
    }
  }
};

const handleShown = () => {
  language.value = previewLang as 'zh' | 'en' ?? 'zh';
  initData();
};

const handleHidden = () => {
  markdownDoc.value = '';
  markdownHtml.value = '';
  docData.value = [];
  docId.value = '';
};

onMounted(() => {
  document.addEventListener('keydown', escHandler);
});

onUnmounted(() => {
  document.removeEventListener('keydown', escHandler);
  // mitt.off('side-toggle');
});

</script>

<style scoped lang="scss">

.main-wrap {
  padding: 24px 24px 0;
  margin-bottom: 24px;
}
</style>
