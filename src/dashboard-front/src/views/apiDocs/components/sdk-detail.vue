<template>
  <!--  sdk内容展示  -->
  <div v-if="sdk" class="data-box wrapper">
    <div class="row-item mb10">
      <div class="key">
        <span class="column-key"> {{ t('SDK包名称') }}: </span>
      </div>
      <div class="value">
        <span class="column-value" v-bk-overflow-tips>{{ sdk.name || sdk.sdk_name || '--' }}</span>
      </div>
    </div>
    <div class="row-item mb10">
      <div class="key">
        <span class="column-key"> {{ t('SDK版本') }}: </span>
      </div>
      <div class="value">
        <span class="column-value" v-bk-overflow-tips>{{ sdk.version || sdk.sdk_version_number || '--' }}</span>
      </div>
    </div>

    <div class="row-item mb10">
      <div class="key">
        <span class="column-key"> {{ t('SDK地址') }}: </span>
      </div>
      <div class="value">
        <bk-popover placement="top" width="600" :disabled="!sdk.url && !sdk.sdk_download_url">
          <main class="column-value vm">{{ sdk.url || sdk.sdk_download_url || '--'}}</main>
          <template #content>
            <div style="white-space: normal;word-break: break-all;">
              {{ sdk.url || sdk.sdk_download_url }}
            </div>
          </template>
        </bk-popover>
      </div>
      <aside class="suffix">
        <i
          class="doc-copy vm icon-hover apigateway-icon icon-ag-copy ag-doc-icon"
          v-if="sdk.url || sdk.sdk_download_url"
          v-bk-tooltips="t('复制')"
          @click="copy(sdk.url || sdk.sdk_download_url)"
        >
        </i>
        <i
          class="ag-doc-icon doc-download-line vm icon-hover apigateway-icon icon-ag-download-line"
          v-if="sdk.url || sdk.sdk_download_url"
          v-bk-tooltips="t('下载')"
          @click="handleDownload">
        </i>
      </aside>
    </div>

    <div class="row-item mb10">
      <div class="key">
        <span class="column-key"> {{ t('安装') }}: </span>
      </div>
      <div class="value">
        <bk-popover placement="top" width="600" v-if="sdk.install_command || sdk.sdk_install_command">
          <main class="column-value vm">{{sdk.install_command || sdk.sdk_install_command}}</main>
          <template #content>
            <div style="white-space: normal;word-break: break-all;">
              {{ sdk.install_command || sdk.sdk_install_command }}
            </div>
          </template>
        </bk-popover>
        <span v-else>--</span>
      </div>
      <aside class="suffix">
        <i
          class="ag-doc-icon doc-copy vm icon-hover apigateway-icon icon-ag-copy"
          v-if="sdk.install_command || sdk.sdk_install_command"
          v-bk-tooltips="t('复制')"
          @click="copy(sdk.install_command || sdk.sdk_install_command)"
        >
        </i>
      </aside>
    </div>

    <template v-if="isApigw && doc">
      <div class="row-item mb10">
        <div class="key">
          <span class="column-key">
            {{ t('资源版本') }}
            <help-fill style="font-size: 16px; margin-left: 4px;" v-bk-tooltips="t('该SDK关联的API资源版本')" />
            :
          </span>
        </div>
        <div class="value">
          <span
            class="column-value"
            v-bk-tooltips.top="{ content: doc.resource_version ?? '--', allowHTML: false }">
            {{ doc.resource_version ?? '--'}}
          </span>
        </div>
      </div>

      <div class="row-item mb10" v-if="doc.stage?.name">
        <div class="key">
          <span class="column-key">
            {{ t('版本已发环境') }}:
          </span>
        </div>
        <div class="value">
          <span class="column-value" v-bk-tooltips.top="doc.stage?.name">{{ doc.stage?.name || '--' }}</span>
        </div>
      </div>
    </template>
  </div>
</template>

<script lang="ts" setup>
import { useI18n } from 'vue-i18n';
import { copy } from '@/common/util';
import { HelpFill } from 'bkui-vue/lib/icon';
import {
  IApiGatewaySdkDoc,
  ISdk,
} from '@/views/apiDocs/types';
import { toRefs } from 'vue';

const { t } = useI18n();

interface IProps {
  isApigw: boolean;
  sdk: ISdk | null
  doc: IApiGatewaySdkDoc | null
}

const props = withDefaults(defineProps<IProps>(), {
  isApigw: false,
  sdk: () => null,
  doc: () => null,
});

const { sdk, doc } = toRefs(props);

const handleDownload = () => {
  if (sdk.value.url || sdk.value.sdk_download_url) {
    window.open(sdk.value.url || sdk.value.sdk_download_url);
  }
};
</script>

<style lang="scss" scoped>
.data-box {
  padding: 12px 16px;
  background: #fafbfd;

  .row-item {
    display: flex;

    .key {
      flex-shrink: 0;
      width: 90px;
      padding-right: 10px;
      text-align: right;
    }

    .value {
      width: calc(100% - 140px);
    }

    .suffix {
      flex-shrink: 0;
      padding-left: 4px;
      width: 50px;
      display: flex;
      align-items: center;
    }
  }
}
.column-key {
  font-size: 14px;
  color: #63656E;
  line-height: 22px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.column-value {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.ag-doc-icon {
  font-size: 16px;
  color: #979BA5;
  cursor: pointer;
  margin-right: 5px;
}

.icon-hover:hover {
  color: #3a84ff;
}
</style>
