<template>
  <div class="component-doc">
    <div class="component-content">
      <div class="component-metedata mb10">
        <strong class="name mr5" v-bk-tooltips.top="curComponent.name">{{curComponent.name || '--'}}</strong>
        <span
          class="label"
          v-bk-tooltips.top="{ content: curComponent.description, allowHTML: false }"
        >
          ({{curComponent.description || t('暂无描述')}})
        </span>
      </div>
      <div style="position: relative;">
        <chat
          class="ag-chat"
          v-if="userStore.featureFlags?.ALLOW_CREATE_APPCHAT"
          :default-user-list="userList"
          :owner="curUser.username"
          :name="chatName"
          :content="chatContent"
          :is-query="true">
        </chat>
      </div>

      <bk-tab v-model:active="active" class="bk-special-tab">
        <bk-tab-panel
          :name="'doc'"
          :label="t('文档')">
          <div class="ag-kv-box mb30">
            <div class="kv-row">
              <div class="k"> {{ t('更新时间') }}：</div>
              <div class="v">{{curDocUpdated || '--'}}</div>
            </div>
            <div class="kv-row">
              <div class="k">
                {{ t('应用认证') }}：
                <i class="ml5 bk-icon icon-question-circle" v-bk-tooltips="t('应用访问该网关API时，是否需提供应用认证信息')">
                </i>
              </div>
              <div class="v">{{curComponent.verified_app_required ? t('是') : t('否')}}</div>
            </div>
            <div class="kv-row">
              <div class="k">
                {{ t('用户认证') }}：
                <i class="ml5 bk-icon icon-question-circle" v-bk-tooltips="t('应用访问该组件API时，是否需要提供用户认证信息')">
                </i>
              </div>
              <div class="v">{{curComponent.verified_user_required ? t('是') : t('否')}}</div>
            </div>
            <div class="kv-row">
              <div class="k">
                {{ t('是否需申请权限') }}：
                <i class="ml5 bk-icon icon-question-circle" v-bk-tooltips="t('应用访问该网关API前，是否需要在开发者中心申请该网关API权限')"></i>
              </div>
              <div class="v">{{curComponent.allow_apply_permission ? t('是') : t('否')}}</div>
            </div>
          </div>
          <!-- eslint-disable-next-line vue/no-v-html -->
          <div class="ag-markdown-view" id="markdown" :key="renderHtmlIndex" v-dompurify-html="curComponent.markdownHtml"></div>
        </bk-tab-panel>
        <!-- <bk-tab-panel
          :name="'sdk'"
          :label="t('SDK及示例')"
          v-if="userStore.featureFlags?.ENABLE_SDK"
        >
          <div id="sdk-markdown">
            <div class="bk-button-group">
              <bk-button class="is-selected">Python</bk-button>
            </div>

            <h3 class="f16">
              {{ t('SDK信息-doc') }}
              <span class="ag-tip ml10" v-if="!curSdk?.sdk?.version">
                ({{ SDKInfo }})
              </span>
            </h3>

            <div>
              <sdk-detail :params="curSdk" :is-apigw="true"></sdk-detail>
            </div>

            <h3 class="f16 mt20"> {{ t('SDK使用样例') }} </h3>
            <div class="ag-markdown-view mt20" :key="renderHtmlIndex" v-dompurify-html="sdkMarkdownHtml"></div>
          </div>
        </bk-tab-panel> -->
      </bk-tab>
    </div>

  </div>
</template>

<script setup lang="ts">
/* eslint-disable max-len */

import { ref, computed, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import { useUser, useCommon } from '@/store';
import { copy } from '@/common/util';
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';
import {
  getApigwResourceSDKDocs,
  getApigwResourceDocDocs,
  getApigwResourcesDocs,
  getApigwSDKDocs,
  getGatewaysDetailsDocs,
} from '@/http';

const { t } = useI18n();
const userStore = useUser();
const common = useCommon();

const props = defineProps({
  stageName: {
    type: String,
  },
  resourceName: {
    type: String,
  },
});

const curSdk = ref<any>({});
const active = ref<string>('doc');
const curComponent = ref<any>({
  id: '',
  name: '',
  label: '',
  content: '',
  innerHtml: '',
  markdownHtml: '',
});
const curApigw = ref({
  name: '',
  label: '',
  maintainers: [],
});
const curDocUpdated = ref<string>('');
const sdkMarkdownHtml = ref<string>('');
const renderHtmlIndex = ref<number>(0);
const sdks = ref<any>([]);

const curUser = computed(() => userStore?.user);
const userList = computed(() => {
  // 去重
  const set = new Set([curUser.value?.username, ...curApigw.value?.maintainers]);
  return [...set];
});
const chatName = computed(() => `${t('[蓝鲸网关API咨询] 网关')}${curApigw.value?.name}`);
const chatContent = computed(() => `${t('网关API文档')}:${location.href}`);
// const SDKInfo = computed(() => t('网关当前环境【{curStageText}】对应的资源版本未生成 SDK，可联系网关负责人生成 SDK', { curStageText: props.stageName }));

const md = new MarkdownIt({
  linkify: false,
  html: true,
  breaks: true,
  highlight(str: string, lang: string) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(lang, str, true).value;
      } catch (__) {}
    }

    return '';
  },
});

const initMarkdownHtml = (box: string) => {
  nextTick(() => {
    const markdownDom = document.getElementById(box);
    // 右侧导航
    // const titles = markdownDom?.querySelectorAll('h3');
    if (box === 'sdk-markdown') {
      // sdkNavList.value = [];
      // const sdkNavArr: any = [];
      // titles?.forEach((item) => {
      //   const name = String(item?.firstChild?.nodeValue).trim();
      //   const id = slugify(name);
      //   item.id = `${curComponentName.value}?${id}`;
      //   sdkNavArr.push({
      //     id: `${curComponentName.value}?${id}`,
      //     name,
      //   });
      // });
      // sdkNavList.value = sdkNavArr;
    } else {
      // componentNavList.value = [];
      // const componentNavArr: any = [];
      // titles?.forEach((item) => {
      //   const name = String(item?.innerText).trim();
      //   const id = slugify(name);
      //   item.id = `${curComponentName.value}?${id}`;
      //   componentNavArr.push({
      //     id: `${curComponentName.value}?${id}`,
      //     name,
      //   });
      // });
      // componentNavList.value = componentNavArr;
    }

    // 复制代码
    markdownDom?.querySelectorAll('a')?.forEach((item) => {
      item.target = '_blank';
    });
    markdownDom?.querySelectorAll('pre')?.forEach((item) => {
      const parentDiv = document.createElement('div');
      const btn = document.createElement('button');
      const codeBox = document.createElement('div');
      const code = item?.querySelector('code')?.innerText;
      parentDiv.className = 'pre-wrapper';
      btn.className = 'ag-copy-btn';
      codeBox.className = 'code-box';
      btn.innerHTML = '<span title="复制"><i class="apigateway-icon icon-ag-copy-info"></i></span>';
      btn.setAttribute('data-copy', code);
      parentDiv?.appendChild(btn);
      codeBox?.appendChild(item?.querySelector('code'));
      item?.appendChild(codeBox);
      item?.parentNode?.replaceChild(parentDiv, item);
      parentDiv?.appendChild(item);
    });


    setTimeout(() => {
      const copyDoms = Array.from(document.getElementsByClassName('ag-copy-btn'));

      const handleCopy = function (this: any) {
        copy(this.dataset?.copy);
      };

      copyDoms.forEach((dom: any) => {
        dom.onclick = handleCopy;
      });
    }, 1000);
  });
};

const getApigwAPIDetail = async () => {
  try {
    const res = await getGatewaysDetailsDocs(common.apigwName);
    curApigw.value = res;
  } catch (e) {
    console.log(e);
  }
};

const getApigwResourceDetail = async () => {
  try {
    const query = {
      limit: 10000,
      offset: 0,
      stage_name: props.stageName,
    };
    const res = await getApigwResourcesDocs(common.apigwName, query);

    const match = res?.find((item: any) => {
      return item.name === props.resourceName;
    });
    if (match) {
      curComponent.value = { ...curComponent.value, ...match };
    }
  } catch (e) {
    console.log(e);
  }
};

const getApigwResourceDoc = async () => {
  try {
    const query = {
      stage_name: props.stageName,
    };
    const res = await getApigwResourceDocDocs(common.apigwName, props.resourceName, query);
    const { content } = res;
    curComponent.value.content = content;
    curComponent.value.markdownHtml = md.render(content);
    renderHtmlIndex.value += 1;
    curDocUpdated.value = res.updated_time;

    initMarkdownHtml('markdown');
  } catch (e) {
    console.log(e);
  } finally {
  }
};

const getApigwResourceSDK = async () => {
  try {
    const query = {
      language: 'python',
      stage_name: props.stageName,
      resource_name: props.resourceName,
    };
    const res = await getApigwResourceSDKDocs(common.apigwName, query);
    const { content } = res;
    sdkMarkdownHtml.value = md.render(content);
    initMarkdownHtml('sdk-markdown');
  } catch (e) {
    console.log(e);
  }
};

const getApigwSDK = async (language: string) => {
  try {
    const query = {
      limit: 10000,
      offset: 0,
      language,
    };
    const res = await getApigwSDKDocs(common.apigwName, query);
    sdks.value = res;
    const match = sdks.value?.find((item: any) => item?.stage?.name === props.stageName);
    curSdk.value = match || {};
    getApigwResourceSDK();
  } catch (e) {
    console.log(e);
  }
};

const init = () => {
  getApigwAPIDetail();
  getApigwResourceDetail();
  getApigwResourceDoc();
  getApigwSDK('python');
};
init();
</script>

<style lang="scss" scoped>
@import '../../apigwDocs/components/detail.css';
.component-content {
  width: 100%;
  max-height: 100%;
}
</style>
