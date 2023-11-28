<template>
  <div class="intro-doc">
    <div class="component-content">
      <div class="component-metedata mb10">
        <strong class="name"> {{ $t('简介') }} </strong>
      </div>

      <div style="position: relative;">
        <bk-breadcrumb separator-class="bk-icon icon-angle-right" class="0">
          <bk-breadcrumb-item :to="{ name: 'apigwDoc' }"> {{ $t('网关API文档') }} </bk-breadcrumb-item>
          <bk-breadcrumb-item>{{curApigw.name || '--'}}</bk-breadcrumb-item>
          <bk-breadcrumb-item> {{ $t('简介') }} </bk-breadcrumb-item>
        </bk-breadcrumb>
        <!-- <chat
          class="ag-chat"
          :default-user-list="userList"
          :owner="curUser.username"
          :name="chatName"
          :content="chatContent"
          :is-query="true">
        </chat> -->
      </div>

      <bk-divider></bk-divider>

      <div class="ag-markdown-view" id="markdown">
        <h3> {{ $t('网关描述') }} </h3>
        <p class="mb30">{{curApigw.description}}</p>

        <h3> {{ $t('网关负责人') }} </h3>
        <p class="mb30">{{curApigw.maintainers.join(', ')}}</p>

        <h3> {{ $t('网关访问地址') }} </h3>
        <p class="mb30">{{curApigw.api_url}}</p>

        <h3> {{ $t('网关 SDK') }} </h3>
        <div class="bk-button-group">
          <bk-button class="is-selected">Python</bk-button>
          <!-- <bk-button disabled>GO</bk-button> -->
        </div>
      </div>

      <bk-table
        style="margin-top: 15px;"
        :data="sdks"
        show-overflow-tooltip
        :size="'small'">
        <template #empty>
          <table-empty
            :abnormal="isAbnormal"
            @reacquire="getApigwSDK('python')"
          />
        </template>

        <bk-table-column :label="$t('网关环境')" field="stage_name">
          <template #default="{ data }">
            {{data?.stage_name}}
          </template>
        </bk-table-column>

        <bk-table-column :label="$t('网关API资源版本')" field="resource_version_display" width="250">
          <template #default="{ data }">
            {{data?.resource_version_display || '--'}}
          </template>
        </bk-table-column>

        <bk-table-column :label="$t('SDK 版本号')" field="sdk_version_number">
          <template #default="{ data }">
            {{data?.sdk_version_number || '--'}}
          </template>
        </bk-table-column>

        <bk-table-column :label="$t('SDK下载')">
          <template #default="{ data }">
            <template v-if="data?.sdk_download_url">
              <bk-button class="mr5" :text="true" @click="handleShow(data)"> {{ $t('查看') }} </bk-button>
              <bk-button :text="true" @click="handleDownload(data)"> {{ $t('下载') }} </bk-button>
            </template>
            <template v-else>
              {{ $t('未生成-doc') }}
            </template>
          </template>
        </bk-table-column>
      </bk-table>

      <p class="ag-tip mt5">
        <i class="bk-icon icon-info"></i>
        {{ $t('若资源版本对应的SDK未生成，可联系网关负责人生成SDK') }}
      </p>

      <!-- <zan class="mt30 mb50"></zan> -->

      <bk-sideslider
        :width="720"
        :title="sdkConfig.title"
        :is-show="sdkConfig.isShow"
        :quick-close="true">
        <template #default>
          <div class="p25">
            <sdk-detail :params="curSdk"></sdk-detail>
          </div>
        </template>
      </bk-sideslider>
    </div>

    <div class="component-nav-box" v-if="componentNavList.length">
      <div style="position: fixed;">
        <side-nav :list="componentNavList"></side-nav>
      </div>
    </div>
  </div>
</template>

<script lang="ts"  setup>
import { ref, reactive, computed, watch, nextTick } from 'vue';
// import Clipboard from 'clipboard'
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';
// import { Message } from 'bkui-vue';
import { slugify } from 'transliteration';
// import Chat from '@/components/chat'
import sdkDetail from '@/components/sdk-detail';
// import zan from '@/components/zan'
import sideNav from '@/components/side-nav';
import { getGatewaysDetailsDocs, getApigwSDKDocs } from '@/http';

const route = useRoute();
const { t } = useI18n();
const sdks = ref<any>([]);
const sdkConfig = reactive({
  title: '',
  isShow: false,
});
const curSdk = ref<any>({});
const componentNavList = ref<any>([]);
const curApigw = ref<any>({
  id: 2,
  name: '',
  description: '',
  maintainers: [
  ],
  is_official: '',
  api_url: '',
});
const isAbnormal = ref<boolean>(false);
const curApigwId = ref();
// const clipboardInstance = ref();


// const curUser = computed(() => this.$store.state.user);
// const userList = computed(() => {
//   // 去重
//   const set = new Set([curUser.value?.username, ...curApigw.value?.maintainers]);
//   return [...set];
// });
// const chatName = computed(() => `${t('[蓝鲸网关API咨询] 网关')}${curApigw.value?.name}`);
// const chatContent = computed(() => `${t('网关API文档')}:${location.href}`);


// const renderHeader = (h, data: any) => {
//   const directive = {
//     name: 'bkTooltips',
//     content: t('网关API资源版本对应的SDK'),
//     placement: 'right',
//   };
//   return (<span style="cursor: pointer;" class="custom-header-cell" v-bk-tooltips={ directive }>
//               { data.column.label }
//               <i class="bk-icon icon-question-circle-shape ml5"></i>
//           </span>)
// };

const handleShow = (data: any) => {
  curSdk.value = data;
  sdkConfig.title = `${t('网关API SDK')}：${curApigwId.value}`;
  sdkConfig.isShow = true;

  // setTimeout(() => {
  //   clipboardInstance.value = new Clipboard('.doc-copy')
  //   clipboardInstance.value.on('success', () => {
  //     Message({
  //       width: 100,
  //       limit: 1,
  //       theme: 'success',
  //       message: t('复制成功')
  //     })
  //   })
  // }, 1000)
};

const handleDownload = (sdk: any) => {
  window.open(sdk?.sdk_download_url);
};

const initMarkdownHtml = () => {
  nextTick(() => {
    const markdownDom = document.getElementById('markdown');
    // 右侧导航
    const titles = markdownDom.querySelectorAll('h3');
    componentNavList.value = [];
    titles.forEach((item) => {
      const name = String(item.innerText).trim();
      const newName = slugify(name);
      // const id = `${curComponentName.value}?${newName}`;
      const id = newName;
      componentNavList.value.push({
        id,
        name,
      });
      item.id = id;
    });

    // 复制代码
    markdownDom.querySelectorAll('a').forEach((item) => {
      item.target = '_blank';
    });
    markdownDom.querySelectorAll('pre').forEach((item) => {
      const btn = document.createElement('button');
      const codeBox = document.createElement('div');
      const code = item.querySelector('code').innerText;
      btn.className = 'ag-copy-btn';
      codeBox.className = 'code-box';
      btn.innerHTML = '<span :title="$t(`复制`)"><i class="bk-icon icon-clipboard mr5"></i></span>';
      btn.setAttribute('data-clipboard-text', code);
      item.appendChild(btn);
      codeBox.appendChild(item.querySelector('code'));
      item.appendChild(codeBox);
    });
  });

  // if (clipboardInstance.value?.off) {
  //   clipboardInstance.value?.off('success')
  // }
  // setTimeout(() => {
  //   clipboardInstance.value = new Clipboard('.doc-copy')
  //   clipboardInstance.value.on('success', () => {
  //     Message({
  //       width: 100,
  //       limit: 1,
  //       theme: 'success',
  //       message: t('复制成功')
  //     })
  //   })
  // }, 1000)
};

const getApigwAPIDetail = async () => {
  try {
    const res = await getGatewaysDetailsDocs(curApigwId.value);
    curApigw.value = res;
    initMarkdownHtml();
  } catch (e) {
    console.log(e);
  } finally {
  }
};

const getApigwSDK = async (language: string) => {
  try {
    const query = {
      limit: 10000,
      offset: 0,
      language,
    };
    const res = await getApigwSDKDocs(curApigwId.value, query);
    sdks.value = res;
    isAbnormal.value = false;
  } catch (e) {
    isAbnormal.value = true;
    console.log(e);
  }
};

const init = async () => {
  const container = document.querySelector('.container-content');
  container.scrollTo({
    top: 0,
    behavior: 'smooth',
  });

  const routeParams = route.params;
  curApigwId.value = routeParams.apigwId;
  getApigwAPIDetail();
  getApigwSDK('python');
};

init();

watch(
  () => route,
  () => {
    init();
  },
  { immediate: true, deep: true },
);
</script>

<style lang="scss" scoped>
  @import './detail.css';
</style>
