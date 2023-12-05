<template>
  <div class="skd-wrapper">
    <bk-tab v-model:active="active" :key="renderKey">
      <bk-tab-panel :name="'sdk'" :label="t('SDK 列表')">
        <div class="bk-button-group">
          <bk-button class="is-selected">Python</bk-button>
          <!-- <bk-button disabled>GO</bk-button> -->
        </div>
        <bk-input
          v-if="type === 'apigateway'" class="fr w500" v-model="keyword" :placeholder="t('请输入网关名称或描述')"
          :right-icon="'bk-icon icon-search'" :clearable="true">
        </bk-input>
        <bk-loading :loading="isLoading">
          <bk-table
            class="sdk-content-table mt15" ref="sdkRef" :data="curPageData" :size="'small'" :key="renderKey"
            :outer-border="false" :pagination="pagination" @page-limit-change="handlePageLimitChange"
            @page-change="handlePageChange">
            <template v-if="type === 'apigateway'">
              <bk-table-column :label="t('网关名称')">
                <template #default="{ data }">
                  {{ data?.gateway.name }}
                </template>
              </bk-table-column>

              <bk-table-column :label="t('网关描述')">
                <template #default="{ data }">
                  <span
                    v-bk-tooltips="{
                      content: data?.gateway.description, placement: 'left', extCls: 'gateway-detail-tooltips',
                      disabled: data?.gateway.description === ''
                    }">
                    {{ data?.gateway.description || '--' }}
                  </span>
                  <!-- <bk-popover
                    placement="left"
                    width="300"
                    theme="dark"
                    :content="data?.gateway.description"
                  >
                    {{ data?.gateway.description || '--' }}
                  </bk-popover> -->
                </template>
              </bk-table-column>
            </template>

            <template v-else>
              <bk-table-column :label="t('名称')">
                <template #default="{ data }">
                  {{ data?.board_label || '--' }}
                </template>
              </bk-table-column>

              <bk-table-column :label="t('描述')">
                <template #default="{ data }">
                  {{ data?.sdk_description || '--' }}
                </template>
              </bk-table-column>
            </template>

            <bk-table-column :label="t('SDK包名称')">
              <template #default="{ data }">
                {{ (type === 'apigateway' ? data?.sdk.name : data?.sdk_version_number) || '--' }}
              </template>
            </bk-table-column>

            <bk-table-column :label="t('SDK最新版本')">
              <template #default="{ data }">
                {{ (type === 'apigateway' ? data?.sdk.version : data?.sdk_version_number) || '--' }}
              </template>
            </bk-table-column>

            <bk-table-column :label="t('操作')" width="200">
              <template #default="{ data }">
                <template v-if="type === 'apigateway' ? data?.sdk.url : data?.sdk_download_url">
                  <bk-button class="mr5" theme="primary" text @click="handleShow(data)">
                    {{ t('查看') }}
                  </bk-button>
                  <a class="ag-link" :href="type === 'apigateway' ? data?.sdk.url : data?.sdk_download_url">
                    {{ t('下载') }}
                  </a>
                </template>
                <template v-else>
                  {{ t('未生成') }}
                </template>
              </template>
            </bk-table-column>
          </bk-table>
        </bk-loading>
      </bk-tab-panel>
      <bk-tab-panel :name="'doc'" :label="t('SDK 说明')">
        <div class="bk-button-group ">
          <bk-button class="is-selected">Python</bk-button>
          <!-- <bk-button disabled>GO</bk-button> -->
        </div>
        <!-- eslint-disable-next-line vue/no-v-html -->
        <div class="ag-markdown-view" id="markdown" :key="renderHtmlIndex" v-html="markdownHtml"></div>
        <div class="ag-markdown-editor">
          <mavon-editor
            ref="markdownRef" v-model="markdownDoc" v-show="isEdited" :language="language" :box-shadow="false"
            :subfield="false" :ishljs="false" :code-style="'monokai'" :tab-size="4" />
        </div>
      </bk-tab-panel>
    </bk-tab>

    <!-- 网关/组件详情sideslider -->
    <bk-sideslider v-model:isShow="sidesliderConfi.isShow" :title="sidesliderConfi.title" quick-close width="750">
      <template #default>
        <div class="p25">
          <div class="bk-button-group mb15">
            <bk-button class="is-selected">Python</bk-button>
            <!-- <bk-button disabled>GO</bk-button> -->
          </div>
          <div class="data-box wrapper">
            <div class="row-item mb10">
              <div class="key">
                <span class="column-key"> {{ t('SDK包名称') }}: </span>
              </div>
              <div class="value">
                <span class="column-value" v-bk-overflow-tips>{{ curParams.sdk_name || '--' }}</span>
              </div>
            </div>
            <div class="row-item mb10">
              <div class="key">
                <span class="column-key"> {{ t('SDK版本') }}: </span>
              </div>
              <div class="value">
                <span class="column-value" v-bk-overflow-tips>{{ curParams.sdk_version_number || '--' }}</span>
              </div>
            </div>

            <div class="row-item mb10">
              <div class="key">
                <span class="column-key"> {{ t('SDK地址') }}: </span>
              </div>
              <div class="value flex-row align-items-center">
                <bk-popover placement="top" width="600" theme="dark">
                  <span class="column-value vm">{{ curParams.sdk_download_url || '--' }}</span>
                  <template #content>
                    <div class="popover-text">
                      {{ curParams.sdk_download_url }}
                    </div>
                  </template>
                </bk-popover>
                <i
                  @click="copy(curParams.sdk_download_url)"
                  class="doc-copy vm icon-hover apigateway-icon icon-ag-copy ag-doc-icon"
                  v-if="curParams.sdk_download_url" v-bk-tooltips="t('复制')"
                  :data-clipboard-text="curParams.sdk_download_url"></i>
                <i
                  class="ag-doc-icon doc-download-line vm icon-hover apigateway-icon icon-ag-download-line"
                  v-if="curParams.sdk_download_url" v-bk-tooltips="t('下载')" @click="handleDownload"></i>
              </div>
            </div>

            <div class="row-item mb10">
              <div class="key">
                <span class="column-key"> {{ t('安装') }}: </span>
              </div>
              <div class="value  flex-row align-items-center">
                <bk-popover placement="top" width="600" theme="dark" :disabled="curParams.sdk_install_command === ''">
                  <span class="column-value vm">{{ curParams.sdk_install_command || '--' }}</span>
                  <template #content>
                    <div class="popover-text">
                      {{ curParams.sdk_install_command }}
                    </div>
                  </template>
                </bk-popover>
                <i
                  @click="copy(curParams.sdk_install_command)"
                  class="ag-doc-icon doc-copy vm icon-hover apigateway-icon icon-ag-copy"
                  v-if="curParams.sdk_install_command" v-bk-tooltips="t('复制')"
                  :data-clipboard-text="curParams.sdk_install_command">
                </i>
              </div>
            </div>

            <template v-if="type === 'apigateway'">
              <div class="row-item mb10">
                <div class="key">
                  <span class="column-key">
                    {{ t('资源版本') }}
                    <span v-bk-tooltips="t('该SDK关联的API资源版本')">
                      <i class="icon apigateway-icon icon-ag-help"></i>
                    </span>
                    :
                  </span>
                </div>
                <div class="value">
                  <span
                    class="column-value"
                    v-bk-tooltips.top="{ content: curParams.resource_version_display, allowHTML: false }">
                    {{ curParams.resource_version_display || '--' }}
                  </span>
                </div>
              </div>

              <div class="row-item mb10" v-if="stageText">
                <div class="key">
                  <span class="column-key">
                    {{ t('版本已发环境') }}:
                  </span>
                </div>
                <div class="value">
                  <span class="column-value" v-bk-tooltips.top="stageText">{{ stageText || '--' }}</span>
                </div>
              </div>
            </template>
          </div>
        </div>

      </template>
    </bk-sideslider>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, reactive, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';
import { copy } from '@/common/util';
import {
  getGatewaySDKlist,
  getESBSDKlist,
  getGatewaySDKDoc,
  getESBSDKDoc,
} from '@/http';

const props = defineProps({
  curType: {
    type: String,
    default: 'apigateway',
  },
});
const { t } = useI18n();
const route = useRoute();

const board = ref<string>('-');
const type = ref<string | any>('');
const sdkDoc = ref<string>('');
const markdownHtml = ref<string>('');
const markdownDoc = ref<string>('');
const language = ref<string>('zh');
const active = ref<string>('sdk');
const renderKey = ref<number>(0);
const renderHtmlIndex = ref<number>(0);
const keyword = ref<string>('');
const isEdited = ref<boolean>(false);
const isLoading = ref<boolean>(false);
const markdownRef = ref(null);
const pagination = ref({
  offset: 0,
  count: 0,
  limit: 10,
});
const sidesliderConfi = reactive({
  isShow: false,
  title: '',
});
const curParams = ref({
  sdk_name: '',
  sdk_version_number: '',
  sdk_download_url: '',
  sdk_install_command: '',
  resource_version_display: '',
  released_stages: [],
});
const curPageData = ref([]);


// 监听搜索关键词的变化
watch(
  () => keyword.value,
  (v: string) => {
    getSDKlist(v);
  },
);

// 获取所有stage的name
const stageText = computed(() => {
  const text = curParams.value.released_stages.map((item: any) => item.name);
  return text.join('，');
});

// 条数变化发生的事件
const handlePageLimitChange = (limit: number) => {
  pagination.value.limit = limit;
  getSDKlist();
};
// 页码变化发生的事件
const handlePageChange = (current: number) => {
  pagination.value.offset = pagination.value.limit * (current - 1);
  getSDKlist();
};

// 查看
const handleShow = (data: any) => {
  console.log(data);
  sidesliderConfi.isShow = true;
  const isGateway = type.value === 'apigateway';
  sidesliderConfi.title = isGateway ? `网关API SDK：${data.gateway.name}` : `组件API SDK：${data.board_label}`;
  curParams.value = {
    sdk_name: isGateway ? data.sdk.name : data.sdk_name,
    sdk_version_number: isGateway ? data.sdk.version : data.sdk_version_number,
    sdk_download_url: isGateway ? data.sdk.url : data.sdk_download_url,
    sdk_install_command: isGateway ? data.sdk.install_command : data.sdk_install_command,
    resource_version_display: isGateway ? data.resource_version.version : '',
    released_stages: isGateway ? data.released_stages : [],
  };
};
// 下载
const handleDownload = () => {
  if (curParams.value.sdk_download_url) {
    window.open(curParams.value.sdk_download_url);
  }
};
const initMarkdownHtml = (content: string) => {
  markdownHtml.value = markdownRef.value.markdownIt.render(content);
};

// 获取SDK list
const getSDKlist = async (keyword: any | string = null) => {
  const pageParams = {
    limit: pagination.value.limit,
    offset: pagination.value.offset,
    language: 'python',
    keyword,
  };
  isLoading.value = true;
  try {
    if (type.value === 'apigateway') {
      const res = await getGatewaySDKlist(pageParams);
      curPageData.value = res.results;
      pagination.value.count = res.count;
    } else {
      const res = await getESBSDKlist(board.value, pageParams);
      curPageData.value = res;
      pagination.value.count = res.length;
    }
    isLoading.value = false;
  } catch (error) {
    console.log('error', error);
  }
};

// 获取SDK 说明
const getSDKDoc = async () => {
  const params = { language: 'python' };
  isLoading.value = true;
  try {
    if (type.value === 'apigateway') {
      const res = await getGatewaySDKDoc(params);
      sdkDoc.value = res.content;
    } else {
      const res = await getESBSDKDoc(board.value, params);
      sdkDoc.value = res.content;
    }
    isLoading.value = false;
    initMarkdownHtml(sdkDoc.value);
  } catch (error) {

  }
};

const init = () => {
  const curTab: any = route.query.tab;
  active.value = curTab ? curTab : 'sdk';
  type.value = props.curType;
  console.log('type', type.value);
  getSDKlist();
  getSDKDoc();
};

// 监听type的变化
watch(
  () => props.curType,
  () => {
    active.value = 'sdk';
    curPageData.value = [];
    // eslint-disable-next-line no-plusplus
    renderKey.value++;
    init();
  },
  { immediate: true, deep: true },
);

</script>

<style lang="scss" scoped>
.w500 {
  width: 500px;
}

.skd-wrapper {
  width: 1200px;
  margin: 20px auto;
  min-height: 100%;
}

:deep(.sdk-content-table) {
  .bk-exception {
    height: 280px;
    max-height: 280px;
    justify-content: center;
  }
}

:deep(.bk-tab-content) {
  background-color: #fff;
  padding: 20px;
}

.column-key {
  font-size: 14px;
  color: #63656E;
  line-height: 22px;
}

.column-value {
  font-size: 14px;
  color: #313238;
  line-height: 22px;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
  max-width: 90%;
  display: inline-block;
}

.ag-doc-icon {
  font-size: 16px;
  color: #979BA5;
  cursor: pointer;
  margin-right: 5px;

  &:hover {
    color: #3A84FF;
  }
}

:deep(.bk-tab-section) {
  padding: 20px !important;
}

:deep(.bk-button-group) {
  .is-selected {
    background-color: #F6F9FF !important;
  }
}

:deep(.ag-markdown-view) {
  font-size: 14px;
  text-align: left;
  color: #63656e;
  line-height: 19px;
  font-style: normal;

  h1,
  h2,
  h3,
  h4,
  h5,
  h6 {
    padding: 0;
    margin: 25px 0 10px 0 !important;
    font-weight: bold;
    text-align: left;
    color: #313238;
    line-height: 21px;
  }

  h1 {
    font-size: 18px;
  }

  h2 {
    font-size: 17px;
  }

  h3 {
    font-size: 16px;
  }

  h4 {
    font-size: 13px;
  }

  h5 {
    font-size: 12px;
  }

  h6 {
    font-size: 12px;
  }

  p {
    font-size: 14px;
    color: #63656E;
    line-height: 22px;
    white-space: normal;
    word-break: break-all;
  }

  ul {
    padding-left: 17px;
    line-height: 22px;

    li {
      list-style: disc;
      margin-bottom: 8px;

      &:last-child {
        margin-bottom: 0;
      }
    }
  }

  ol {
    padding-left: 15px;
    line-height: 22px;
    margin: 14px 0;

    li {
      list-style: decimal;
      margin-bottom: 8px;

      &:last-child {
        margin-bottom: 0;
      }
    }
  }

  a {
    color: #3A84FF;
  }

  tt {
    margin: 0 2px;
    padding: 0 5px;
    white-space: nowrap;
    border: 1px solid #eaeaea;
    background-color: #f8f8f8;
    border-radius: 3px;
    font-size: 75%;
  }

  table {
    font-size: 14px;
    color: #63656E;
    width: 100%;
    text-align: left;
    border: none;
    margin: 10px 0;
    font-style: normal;
    border: 1px solid #DCDEE5;

    &.field-list {
      th {
        width: 12%;
      }
    }

    em {
      font-style: normal;
    }

    th {
      background: #F0F1F5;
      font-size: 13px;
      font-weight: bold;
      color: #63656E;
      border-bottom: 1px solid #DCDEE5;
      padding: 10px;
      min-width: 70px;

    }

    th:nth-child(1) {
      width: 20%;
    }

    td {
      padding: 10px;
      font-size: 13px;
      color: #63656E;
      border-bottom: 1px solid #DCDEE5;
      max-width: 250px;
      font-style: normal;
      word-break: break-all;
    }
  }

  pre {
    border-radius: 2px;
    background: #23241f;
    padding: 10px;
    font-size: 14px;
    text-align: left;
    color: #FFF;
    line-height: 24px;
    position: relative;
    overflow: auto;
    margin: 14px 0;

    code {
      color: #FFF;
    }

    .hljs {
      margin: -10px;
    }
  }
}


.popover-text {
  white-space: normal;
  word-break: break-all;
}

.data-box {
  .row-item {
    display: flex;

    .key {
      width: 170px;
      text-align: right;
      padding-right: 10px;
    }

    .value {
      flex: 1;
      white-space: nowrap;
    }
  }
}

.column-key {
  font-size: 14px;
  color: #63656E;
  line-height: 22px;
}

.column-value {
  font-size: 14px;
  color: #313238;
  line-height: 22px;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
  max-width: 460px;
  display: inline-block;
}

.ag-doc-icon {
  font-size: 16px;
  color: #979BA5;
  cursor: pointer;
  margin-right: 5px;
}

.wrapper {
  margin-top: 10px;
  padding: 10px 5px;
  background: #fafbfd;
}

.icon-hover:hover {
  color: #3a84ff;
}
</style>
<style lang="scss">
.gateway-detail-tooltips {
  width: 300px;
}
</style>


