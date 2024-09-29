<template>
  <div class="res-doc-container">
    <bk-sideslider
      v-model:isShow="isShow"
      quick-close
      :title="resource.name"
      width="780"
      v-bind="$attrs"
      @shown="handleShown()"
      @hidden="handleHidden()"
    >
      <template #default>
        <bk-loading :loading="isLoading">
          <main class="main-wrap">
            <div class="ag-markdown-view" :class="isEdited ? '' : 'text-c'">
              <h3 v-if="isEdited"> {{ $t('文档类型') }} </h3>
              <template v-if="isEdited">
                <p class="pb15">{{ language === 'zh' ? t('中文文档') : t('英文文档') }}</p>
              </template>
              <bk-button-group v-else>
                <bk-button
                  v-for="item in languagesData"
                  :selected="language === item.value"
                  :key="item.value"
                  :disabled="isEdited && language !== item.value"
                  @click="handleSelectLanguage(item.value as 'zh' | 'en')"
                >
                  <div>
                    {{ item.label }}
                  </div>
                </bk-button>
              </bk-button-group>
            </div>
            <div v-show="isEmpty">
              <div class="text-c mt50">
                <bk-exception
                  class="exception-wrap-item exception-part"
                  type="empty"
                  scene="part"
                  :description="language === 'zh' ? t('您尚未创建中文文档') : t('您尚未创建英文文档')"
                />
                <bk-button
                  v-if="showCreateBtn"
                  class="mt20"
                  theme="primary"
                  style="width: 120px;"
                  @click="handleEditMarkdown('create')"
                > {{ t('立即创建') }}
                </bk-button>
              </div>
            </div>
            <div v-show="!isEmpty">
              <div class="ag-markdown-view">
                <h3> {{ language === 'zh' ? $t('请求方法/请求路径') : 'Method/Path' }} </h3>
                <p class="pb15">
                  <span class="ag-tag" :class="resource.method.toLowerCase()">{{ resource.method }}</span>
                  {{ resource.path }}
                </p>
              </div>
              <!-- eslint-disable vue/no-v-html -->
              <div class="ag-markdown-view" v-dompurify-html="markdownHtml" v-show="!isEdited"></div>
              <div class="ag-markdown-editor" v-show="isEdited">
                <mavon-editor
                  ref="markdownRef"
                  :class="{ 'content-editor': !isFullscreen }"
                  v-model="markdownDoc"
                  :language="language"
                  :box-shadow="false"
                  :subfield="false"
                  :ishljs="true"
                  :code-style="'monokai'"
                  :toolbars="toolbars"
                  :tab-size="4"
                  @full-screen="handleFullscreen"
                />
              </div>
            </div>
          </main>
        </bk-loading>
      </template>
      <!--  底部按钮  -->
      <template #footer v-if="showFooter && !isLoading && !isEmpty">
        <div>
          <template v-if="isEdited">
            <bk-button
              class="mr8" theme="primary" style="width: 100px;"
              @click="handleSaveMarkdown"
              :loading="isSaving"
            >{{ isUpdate ? $t('更新') : $t('提交') }}
            </bk-button>
            <bk-button
              style="width: 100px;"
              @click="handleCancelMarkdown"
            > {{ $t('取消') }}
            </bk-button>
          </template>
          <template v-else>
            <bk-button class="mr8" theme="primary" style="width: 100px;" @click="handleEditMarkdown('edit')">
              {{ $t('修改') }}
            </bk-button>
            <bk-pop-confirm
              :title="t('确认要删除该文档？')"
              content="将删除相关配置，不可恢复，请确认是否删除"
              width="288"
              trigger="click"
              @confirm="handleDeleteMarkdown"
            >
              <bk-button>
                {{ t('删除') }}
              </bk-button>
            </bk-pop-confirm>
          </template>
        </div>
      </template>
    </bk-sideslider>
  </div>
</template>
<script setup lang="ts">
import {
  defineModel,
  onMounted,
  onUnmounted,
  ref,
  toRefs,
} from 'vue';
import { cloneDeep } from 'lodash';
import {
  deleteResourceDocs,
  getResourceDocPreview,
  getResourceDocs,
  saveResourceDocs,
  updateResourceDocs,
} from '@/http';
import { Message } from 'bkui-vue';
import { useCommon } from '@/store';
import { useI18n } from 'vue-i18n';
import mitt from '@/common/event-bus';

const { t } = useI18n();
const common = useCommon();
const { apigwId } = common; // 网关id

const props = defineProps({
  resource: { type: Object, default: () => ({}) },
  showFooter: { type: Boolean, default: true }, // 是否显示底部按钮
  showCreateBtn: { type: Boolean, default: true }, // 是否显示"立即创建"按钮
  isPreview: { type: Boolean, default: false }, // 是否获取预览文档，决定调用的接口
  previewLang: { type: [String, null], default: null },
});

const isShow = defineModel<boolean>({
  required: true,
  default: false,
});

const {
  resource,
  showFooter,
  showCreateBtn,
} = toRefs(props);

const languagesData = ref([{ label: t('中文文档'), value: 'zh' }, { label: t('英文文档'), value: 'en' }]);
const isEmpty = ref(false);
const isUpdate = ref(false);
const markdownDoc = ref('');
const markdownHtml = ref('');
const docData = ref<any[]>([]);
const isEdited = ref(false);   // 是否是编辑
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

const emit = defineEmits(['fetch', 'on-update']);

// 编辑markdown
const handleEditMarkdown = (type: string) => {
  isEmpty.value = false;
  isEdited.value = true;

  isUpdate.value = type === 'edit';    // 是否是更新
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
  if (!props.isPreview) {
    docData.value = await getResourceDocs(apigwId, resource.value.id);
  } else {
    // 预览资源文档会走到这里
    const { backend, doc, _localId, _unchecked, ...restOfCurResource } = resource.value;

    const params = {
      review_resource: {
        ...restOfCurResource,
        backend_name: backend.name,
        backend_config: { ...backend.config },
      },
      doc_language: props.previewLang ?? language.value,
    };

    const res = await getResourceDocPreview(apigwId, params);

    docData.value.push({
      id: null,
      language: props.previewLang ?? language.value,
      content: res.doc,
    });
  }
  // 根据语言找到是否有文档内容
  handleDocDataWithLanguage();
  isLoading.value = false;
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
      await updateResourceDocs(apigwId, resource.value.id, data, docId.value);
    } else {
      // 新增
      await saveResourceDocs(apigwId, resource.value.id, data);
    }
    isEdited.value = false;
    Message({
      theme: 'success',
      message: t('保存成功！'),
    });
    initData();
    // 执行列表的方法
    emit('fetch');
  } catch (error) {

  } finally {
    isSaving.value = false;
  }
};

const handleCancelMarkdown = () => {
  isEdited.value = false;
  emit('on-update', 'cancel');
};

// 删除文档
const handleDeleteMarkdown = async () => {
  try {
    await deleteResourceDocs(apigwId, resource.value.id, docId.value);
    Message({
      message: t('删除成功'),
      theme: 'success',
    });
    initData();
    // 执行列表的方法
    emit('fetch');
  } catch (error) {
    console.log('error', error);
  }
};

const handleSelectLanguage = (payload: 'zh' | 'en') => {
  // 如果相同 则return
  if (payload === language.value) return;
  language.value = payload;
  handleDocDataWithLanguage();
};

// 根据语言找到是否有文档内容
const handleDocDataWithLanguage = () => {
  if (!props.isPreview) {
    const docDataItem = cloneDeep(docData.value)
      .find((e: any) => e.language === language.value);
    docId.value = docDataItem.id;
    isEmpty.value = !docDataItem.id;
    markdownDoc.value = docDataItem.content;
    markdownHtml.value = markdownRef.value.markdownIt.render(docDataItem.content);
  } else {
    // 预览资源文档会走到这里
    const doc = docData.value.find((d: any) => d.language === language.value);
    const content = doc?.content ?? '';
    markdownDoc.value = content;
    markdownHtml.value = markdownRef.value.markdownIt.render(content);
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
  language.value = props.previewLang as 'zh' | 'en' ?? 'zh';
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
  mitt.off('side-toggle');
});

</script>
<style scoped lang="scss">

.main-wrap {
  padding: 24px 24px 0 24px;
  margin-bottom: 24px;
}
</style>
