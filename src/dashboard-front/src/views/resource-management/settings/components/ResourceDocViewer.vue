<template>
  <div
    class="resources-doc-container"
    :class="[docRootClass]"
    :style="resourcesHeight"
  >
    <section class="content p-20px">
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
        <BkButtonGroup v-else>
          <BkButton
            v-for="item in languagesData"
            :key="item.value"
            :selected="language === item.value"
            :disabled="isEdited && language !== item.value"
            @click="handleSelectLanguage(item.value)"
          >
            <div>
              {{ item.label }}
            </div>
          </BkButton>
        </BkButtonGroup>
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
              :class="curResource.method.toLowerCase()"
            >{{ curResource.method }}</span>
            {{ curResource.path }}
          </p>
        </div>
        <div
          v-show="!isEdited"
          v-dompurify-html="markdownHtml"
          class="ag-markdown-view pb-54px"
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
            ishljs
            code-style="vs2015"
            :toolbars="toolbars"
            :tab-size="4"
            @full-screen="handleFullscreen"
          />
        </div>
      </div>
    </section>
    <template v-if="showFooter && !isEmpty">
      <div
        v-if="isAdsorb"
        class="doc-btn-wrapper"
        :class="[`${docRootClass}-btn`]"
      >
        <template v-if="isEdited">
          <BkButton
            class="mr-5px w-100px"
            theme="primary"
            :loading="isSaving"
            @click="handleSaveMarkdown"
          >
            {{ isUpdate ? t('更新') : t('提交') }}
          </BkButton>
          <BkButton
            class="w-100px"
            @click="handleCancelMarkdown"
          >
            {{ t('取消') }}
          </BkButton>
        </template>
        <template v-else>
          <BkButton
            class="mr-5px w-100px"
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
            <BkButton>
              {{ t('删除') }}
            </BkButton>
          </BkPopConfirm>
        </template>
      </div>
      <div
        v-else
        class="fixed-doc-btn-wrapper"
        :style="fixedBtnLeft"
      >
        <template v-if="isEdited">
          <BkButton
            class="mr-5px w-100px"
            theme="primary"
            :loading="isSaving"
            @click="handleSaveMarkdown"
          >
            {{ isUpdate ? t('更新') : t('提交') }}
          </BkButton>
          <BkButton
            class="w-100px"
            @click="handleCancelMarkdown"
          >
            {{ t('取消') }}
          </BkButton>
        </template>
        <template v-else>
          <BkButton
            class="mr-5px w-100px"
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
            <BkButton>
              {{ t('删除') }}
            </BkButton>
          </BkPopConfirm>
        </template>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import {
  deleteResourceDocs,
  getResourceDocPreview,
  getResourceDocs,
  saveResourceDocs,
  updateResourceDocs,
} from '@/services/source/resource';
import { useStage } from '@/stores';
import { cloneDeep } from 'lodash-es';
import { Message } from 'bkui-vue';
import { useRouteParams } from '@vueuse/router';
// import mitt from '@/common/event-bus';

interface IProps {
  curResource?: Record<string, any>
  height?: string
  source?: string
  docRootClass?: string
  showFooter?: boolean
  showCreateBtn?: boolean
  isPreview?: boolean
}

const {
  curResource = {},
  // height = 'calc(100vh - 104px)',
  source = '', // side 侧边栏引用
  docRootClass = '',
  // 自定义类
  showFooter = true,
  // 是否显示底部按钮
  showCreateBtn = true,
  // 是否显示"立即创建"按钮
  isPreview = false, // 是否获取预览文档，决定调用的接口
} = defineProps<IProps>();

const emit = defineEmits<{
  'fetch': [void]
  'on-update': [type: string, isUpdate?: boolean]
}>();

const { t } = useI18n();
const stageStore = useStage();
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
const language = ref('zh');
const isSaving = ref(false);
const docId = ref<any>('');
// const hasResourceDoc = ref(false); // 是否有文档内容
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

const resourcesHeight = computed(() => {
  if (source === 'side') {
    return 'height: calc(100vh - 57px)';
  }
  if (stageStore.getNotUpdatedStages?.length) {
    return 'height: calc(100vh - 218px)';
  }
  return 'height: calc(100vh - 176px)';
});

const fixedBtnLeft = computed(() => {
  if (source === 'side') {
    return 'padding-left: 20px';
  }
  return 'padding-left: 30px';
});

// 编辑markdown
const handleEditMarkdown = (type: string) => {
  isEmpty.value = false;
  isEdited.value = true;

  isUpdate.value = type === 'edit'; // 是否是更新
  emit('on-update', 'update', isUpdate.value);
  const docDataItem = cloneDeep(docData.value).find((e: any) => e.language === language.value);
  markdownDoc.value = docDataItem.content;
  controlToggle();
};

const isFullscreen = ref(false);
const handleFullscreen = (full: boolean) => {
  isFullscreen.value = full;
};

// 获取文档信息
const initData = async () => {
  if (!isPreview) {
    docData.value = await getResourceDocs(gatewayId.value, curResource.id);
  }
  else {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { backend, doc, _localId, _unchecked, ...restOfCurResource } = curResource;

    const params = {
      review_resource: {
        ...restOfCurResource,
        backend_name: backend.name,
        backend_config: { ...backend.config },
      },
      doc_language: language.value,
    };

    const res = await getResourceDocPreview(gatewayId.value, params);
    docData.value.push({
      id: null,
      language: language.value,
      content: res.doc,
    });
  }
  // 根据语言找到是否有文档内容
  handleDocDataWithLanguage();
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
      await updateResourceDocs(gatewayId.value, curResource.id, data, docId.value);
    }
    else {
      // 新增
      await saveResourceDocs(gatewayId.value, curResource.id, data);
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
  await deleteResourceDocs(gatewayId.value, curResource.id, docId.value);
  Message({
    message: t('删除成功'),
    theme: 'success',
  });
  initData();
  // 执行列表的方法
  emit('fetch');
  controlToggle();
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
  if (!isPreview) {
    const docDataItem = cloneDeep(docData.value).find((e: any) => e.language === language.value);
    docId.value = docDataItem.id;
    isEmpty.value = !docDataItem.id;
    markdownDoc.value = docDataItem.content;
    markdownHtml.value = markdownRef.value?.markdownIt.render(docDataItem.content);
  }
  else {
    // 预览资源文档会走到这里
    const content = docData.value[0]?.content ?? '';
    markdownDoc.value = content;
    markdownHtml.value = markdownRef.value?.markdownIt.render(content);
  }
};

// 是否吸附
const isAdsorb = ref(false);

// 元素滚动判断元素是否吸顶
const controlToggle = () => {
  const el = document.querySelector(`.${docRootClass}-btn`);
  const bottomDistance = el?.getBoundingClientRect()?.bottom;
  // 是否吸附
  if (bottomDistance > window?.innerHeight) {
    isAdsorb.value = true;
    el?.classList?.add('is-pinned');
  }
  else {
    isAdsorb.value = false;
    el?.classList?.remove('is-pinned');
  }
};

let resizeObserver: any = null;
const observerBtnScroll = () => {
  const container = document.querySelector(`.${docRootClass}`);
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
  const container = document.querySelector(`.${docRootClass}`);
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

  // mitt.on('side-toggle', () => {
  //   controlToggle();
  // });
});

onUnmounted(() => {
  document.removeEventListener('keydown', escHandler);
  // mitt.off('side-toggle');
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
  display: flex;
  width: 100%;
  padding-left: 20px;
  margin-top: 8px;
  background: #fff;
  align-items: center;
}

.fixed-doc-btn-wrapper {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 1600;
  padding: 10px 0;
  background: #fff;
  box-shadow: 0 -2px 4px 0 #0000000f;

  // transition: .3s;

  :deep(.bk-button) {
    margin-right: 1px !important;
  }
}

.is-pinned {
  opacity: 0%;
}
</style>
