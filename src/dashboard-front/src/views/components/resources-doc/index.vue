<template>
  <div :class="['resources-doc-container', docRootClass]" :style="resourcesHeight">
    <section class="content p20">
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
            @click="handleSelectLanguage(item.value)"
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
          > {{ t('立即创建') }} </bk-button>
        </div>
      </div>
      <div v-show="!isEmpty">
        <div class="ag-markdown-view">
          <h3> {{ language === 'zh' ? $t('请求方法/请求路径') : 'Method/Path' }} </h3>
          <p class="pb15">
            <span class="ag-tag" :class="curResource.method.toLowerCase()">{{curResource.method}}</span>
            {{curResource.path}}
          </p>
        </div>
        <!-- eslint-disable vue/no-v-html -->
        <div class="ag-markdown-view" v-dompurify-html="markdownHtml" v-show="!isEdited" style="padding-bottom: 54px;"></div>
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
    </section>
    <template v-if="showFooter && !isEmpty">
      <div :class="['doc-btn-wrapper', `${docRootClass}-btn`]" v-if="isAdsorb">
        <template v-if="isEdited">
          <bk-button
            class="mr5" theme="primary" style="width: 100px;"
            @click="handleSaveMarkdown"
            :loading="isSaving">{{isUpdate ? $t('更新') : $t('提交')}}</bk-button>
          <bk-button
            style="width: 100px;"
            @click="handleCancelMarkdown"> {{ $t('取消') }} </bk-button>
        </template>
        <template v-else>
          <bk-button class="mr5" theme="primary" style="width: 100px;" @click="handleEditMarkdown('edit')">
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
      <div v-else class="fixed-doc-btn-wrapper" :style="fixedBtnLeft">
        <template v-if="isEdited">
          <bk-button
            class="mr5" theme="primary" style="width: 100px;"
            @click="handleSaveMarkdown"
            :loading="isSaving">{{isUpdate ? $t('更新') : $t('提交')}}</bk-button>
          <bk-button
            style="width: 100px;"
            @click="handleCancelMarkdown"> {{ $t('取消') }} </bk-button>
        </template>
        <template v-else>
          <bk-button class="mr5" theme="primary" style="width: 100px;" @click="handleEditMarkdown('edit')">
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
  </div>
</template>
<script setup lang="ts">
import { ref, toRefs, onMounted, onUnmounted, onBeforeUnmount, nextTick, onUpdated, computed } from 'vue';
import {
  getResourceDocs,
  getResourceDocPreview,
  updateResourceDocs,
  saveResourceDocs,
  deleteResourceDocs,
} from '@/http';
import { useCommon } from '@/store';
import { cloneDeep } from 'lodash';
import { useI18n } from 'vue-i18n';
import { Message } from 'bkui-vue';
import mitt from '@/common/event-bus';

const { t } = useI18n();
const common = useCommon();
const { apigwId } = common; // 网关id
const props = defineProps({
  curResource: { type: Object, default: {} },   // 当前点击的资源
  height: { type: String, default: 'calc(100vh - 104px)' },
  source: { type: String }, // side 侧边栏引用
  docRootClass: { type: String }, // 自定义类
  showFooter: { type: Boolean, default: true }, // 是否显示底部按钮
  showCreateBtn: { type: Boolean, default: true }, // 是否显示"立即创建"按钮
  isPreview: { type: Boolean, default: false }, // 是否获取预览文档，决定调用的接口
});

const {
  curResource,
  showFooter,
  showCreateBtn,
} = toRefs(props);

const languagesData = ref([{ label: t('中文文档'), value: 'zh' }, { label: t('英文文档'), value: 'en' }]);
const isEmpty = ref<boolean>(false);
const isUpdate = ref<boolean>(false);
const markdownDoc = ref<string>('');
const markdownHtml = ref<string>('');
const docData = ref<any[]>([]);
const isEdited = ref<boolean>(false);   // 是否是编辑
const language = ref<string>('zh');
const isSaving = ref<boolean>(false);
const docId = ref<any>('');
// const hasResourceDoc = ref<boolean>(false); // 是否有文档内容
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

const resourcesHeight = computed(() => {
  if (props.source === 'side') {
    return 'height: calc(100vh - 57px)';
  }
  return 'height: calc(100vh - 176px)';
});

const fixedBtnLeft = computed(() => {
  if (props.source === 'side') {
    return 'padding-left: 20px';
  }
  return 'padding-left: 30px';
});

// 编辑markdown
const handleEditMarkdown = (type: string) => {
  isEmpty.value = false;
  isEdited.value = true;

  isUpdate.value = type === 'edit';    // 是否是更新
  emit('on-update', 'update', isUpdate.value);
  const docDataItem = cloneDeep(docData.value).find((e: any) => e.language === language.value);
  markdownDoc.value = docDataItem.content;
  controlToggle();
};

const isFullscreen = ref<Boolean>(false);
const handleFullscreen = (full: Boolean) => {
  isFullscreen.value = full;
};

// 获取文档信息
const initData = async () => {
  try {
    if (!props.isPreview) {
      docData.value = await getResourceDocs(apigwId, curResource.value.id);
    } else {
      const { backend, doc, _localId, _unchecked, ...restOfCurResource } = curResource.value;

      const params = {
        review_resource: {
          ...restOfCurResource,
          backend_name: backend.name,
          backend_config: { ...backend.config },
        },
        doc_language: language.value,
      };

      const res = await getResourceDocPreview(apigwId, params);
      docData.value.push({
        id: null,
        language: language.value,
        content: res.doc,
      });
    }
    // 根据语言找到是否有文档内容
    handleDocDataWithLanguage();
  } catch (error) {
    console.log('error', error);
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
      await updateResourceDocs(apigwId, curResource.value.id, data, docId.value);
    } else {
      // 新增
      await saveResourceDocs(apigwId, curResource.value.id, data);
    }
    isEdited.value = false;
    Message({
      theme: 'success',
      message: t('保存成功！'),
    });
    controlToggle();
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
    await deleteResourceDocs(apigwId, curResource.value.id, docId.value);
    Message({
      message: t('删除成功'),
      theme: 'success',
    });
    initData();
    // 执行列表的方法
    emit('fetch');
    controlToggle();
  } catch (error) {
    console.log('error', error);
  }
};

const handleSelectLanguage = (payload: string) => {
  // 如果相同 则return
  if (payload === language.value) return;
  language.value = payload;
  handleDocDataWithLanguage();
  controlToggle();
};

// 根据语言找到是否有文档内容
const handleDocDataWithLanguage = () => {
  if (!props.isPreview) {
    const docDataItem =  cloneDeep(docData.value).find((e: any) => e.language === language.value);
    docId.value = docDataItem.id;
    isEmpty.value = !docDataItem.id;
    markdownDoc.value = docDataItem.content;
    markdownHtml.value = markdownRef.value.markdownIt.render(docDataItem.content);
  } else {
    // 预览资源文档会走到这里
    const content = docData.value[0]?.content ?? '';
    markdownDoc.value = content;
    markdownHtml.value = markdownRef.value.markdownIt.render(content);
  }
};

// 是否吸附
const isAdsorb = ref<boolean>(false);

// 元素滚动判断元素是否吸顶
const controlToggle = () => {
  const el = document.querySelector(`.${props.docRootClass}-btn`);
  const bottomDistance = el?.getBoundingClientRect()?.bottom;
  // 是否吸附
  if (bottomDistance > window?.innerHeight) {
    isAdsorb.value = true;
    el?.classList?.add('is-pinned');
  } else {
    isAdsorb.value = false;
    el?.classList?.remove('is-pinned');
  }
};

let resizeObserver: any = null;
const observerBtnScroll = () => {
  const container = document.querySelector(`.${props.docRootClass}`);
  container?.addEventListener('scroll', controlToggle);

  if (resizeObserver) {
    resizeObserver.disconnect();
  }
  const parentDom = document.querySelector('.resource-container-rg');
  resizeObserver = new ResizeObserver(() => {
    controlToggle();
  });
  resizeObserver?.observe(parentDom);
};

const destroyEvent = () => {
  const container = document.querySelector(`.${props.docRootClass}`);
  container?.removeEventListener('scroll', controlToggle);

  resizeObserver.disconnect();
};

const escHandler = (e: KeyboardEvent) => {
  if (e.code === 'Escape') {
    if (markdownRef.value?.s_fullScreen) {
      markdownRef.value.s_fullScreen = false;
    }
  }
};

onMounted(() => {
  initData();
  // 初始化判断按钮组是否吸附
  controlToggle();
  nextTick(() => {
    observerBtnScroll();
  });

  document.addEventListener('keydown', escHandler);

  mitt.on('side-toggle', () => {
    controlToggle();
  });
});

onUnmounted(() => {
  document.removeEventListener('keydown', escHandler);

  mitt.off('side-toggle');
});

onUpdated(() => {
  controlToggle();
});

onBeforeUnmount(() => {
  destroyEvent();
});
</script>
<style scoped lang="scss">
.resources-doc-container {
  overflow-y: auto;

  .content {
    height: calc(100% - 50px);
  }
}

.ag-markdown-editor {
  height: calc(100vh - 300px);
}

.content-editor {
  height: 100%;
}

// 把编辑器多余高度的背景色涂成和编辑区一样
:deep(.v-note-wrapper .v-note-panel .v-note-edit.divarea-wrapper.single-edit) {
  background-color: #313238;
}

.doc-btn-wrapper {
  margin-top: 8px;
  background: #fff;
  padding-left: 20px;
  width: 100%;
  display: flex;
  align-items: center;
}
.fixed-doc-btn-wrapper {
  position: absolute;
  bottom: 0;
  right: 0px;
  left: 0;
  padding: 10px 0;
  background: #fff;
  box-shadow: 0 -2px 4px 0 #0000000f;
  z-index: 1600;
  // transition: .3s;
  :deep(.bk-button) {
    margin-right: 1px !important;
  }
}
.is-pinned {
  opacity: 0;
}
</style>
