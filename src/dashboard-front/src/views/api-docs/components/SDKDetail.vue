<template>
  <!--  sdk内容展示  -->
  <div class="data-box wrapper">
    <div class="row-item mb-10px">
      <div class="key">
        <span class="column-key"> {{ t('SDK包名称') }}: </span>
      </div>
      <div class="value">
        <span
          v-bk-overflow-tips
          class="column-value"
        >{{ sdk.name || sdk.sdk_name || '--' }}</span>
      </div>
    </div>
    <div
      v-if="sdk.sdk_description"
      class="row-item mb-10px"
    >
      <div class="key">
        <span class="column-key"> {{ t('SDK描述') }}: </span>
      </div>
      <div class="value">
        <span
          v-bk-overflow-tips
          class="column-value"
        >{{ sdk.sdk_description || '--' }}</span>
      </div>
    </div>
    <div class="row-item mb-10px">
      <div class="key">
        <span class="column-key"> {{ t('SDK版本') }}: </span>
      </div>
      <div class="value">
        <span
          v-bk-overflow-tips
          class="column-value"
        >{{ sdk.version || sdk.sdk_version_number || '--' }}</span>
      </div>
    </div>

    <div class="row-item mb-10px">
      <div class="key">
        <span class="column-key"> {{ t('SDK地址') }}: </span>
      </div>
      <div class="value">
        <BkPopover
          placement="top"
          width="600"
          :disabled="!sdk.url && !sdk.sdk_download_url"
        >
          <main class="column-value ">
            {{ sdk.url || sdk.sdk_download_url || '--' }}
          </main>
          <template #content>
            <div class="break-all whitespace-normal">
              {{ sdk.url || sdk.sdk_download_url }}
            </div>
          </template>
        </BkPopover>
      </div>
      <aside class="suffix">
        <i
          v-if="sdk.url || sdk.sdk_download_url"
          v-bk-tooltips="t('复制')"
          class="doc-copy  icon-hover apigateway-icon icon-ag-copy ag-doc-icon"
          @click="copy(sdk.url || sdk.sdk_download_url)"
        />
        <i
          v-if="sdk.url || sdk.sdk_download_url"
          v-bk-tooltips="t('下载')"
          class="ag-doc-icon doc-download-line  icon-hover apigateway-icon icon-ag-download-line"
          @click="handleDownload"
        />
      </aside>
    </div>

    <div class="row-item mb-10px">
      <div class="key">
        <span class="column-key"> {{ t('安装') }}: </span>
      </div>
      <div class="value">
        <BkPopover
          v-if="sdk.install_command || sdk.sdk_install_command"
          placement="top"
          width="600"
        >
          <main class="column-value ">
            {{ sdk.install_command || sdk.sdk_install_command }}
          </main>
          <template #content>
            <div class="break-all whitespace-normal">
              {{ sdk.install_command || sdk.sdk_install_command }}
            </div>
          </template>
        </BkPopover>
        <span v-else>--</span>
      </div>
      <aside class="suffix">
        <i
          v-if="sdk.install_command || sdk.sdk_install_command"
          v-bk-tooltips="t('复制')"
          class="ag-doc-icon doc-copy icon-hover apigateway-icon icon-ag-copy"
          @click="() => copy(sdk.install_command || sdk.sdk_install_command)"
        />
      </aside>
    </div>

    <template v-if="isApigw && doc">
      <div class="row-item mb-10px">
        <div class="key">
          <span class="column-key">
            {{ t('资源版本') }}
            <HelpFill
              v-bk-tooltips="t('该SDK关联的API资源版本')"
              class="ml-4px! text-16px!"
            />
            :
          </span>
        </div>
        <div class="value">
          <span
            v-bk-tooltips.top="{ content: doc.resource_version ?? '--', allowHTML: false }"
            class="column-value"
          >
            {{ doc.resource_version ?? '--' }}
          </span>
        </div>
      </div>

      <div
        v-if="doc.stage?.name"
        class="row-item mb-10px"
      >
        <div class="key">
          <span class="column-key">
            {{ t('版本已发环境') }}:
          </span>
        </div>
        <div class="value">
          <span
            v-bk-tooltips.top="doc.stage?.name"
            class="column-value"
          >{{ doc.stage?.name || '--' }}</span>
        </div>
      </div>
    </template>
  </div>
</template>

<script lang="ts" setup>
import { copy } from '@/utils';
import { HelpFill } from 'bkui-vue/lib/icon';
import type {
  IApiGatewaySdkDoc,
  ISdk,
} from '../types.d.ts';

const {
  isApigw = false,
  sdk = null,
  doc = null,
} = defineProps<IProps>();

const { t } = useI18n();

interface IProps {
  isApigw: boolean
  sdk: ISdk | null
  doc: IApiGatewaySdkDoc | null
}

const handleDownload = () => {
  if (sdk.url || sdk.sdk_download_url) {
    window.open(sdk.url || sdk.sdk_download_url);
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
      display: flex;
      width: 50px;
      padding-left: 4px;
      flex-shrink: 0;
      align-items: center;
    }
  }
}

.column-key {
  display: flex;
  font-size: 14px;
  line-height: 22px;
  color: #63656E;
  align-items: center;
  justify-content: flex-end;
}

.column-value {
  display: -webkit-box;
  overflow: hidden;
  word-break: break-all;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 1;
  line-clamp: 1;
}

.ag-doc-icon {
  margin-right: 5px;
  font-size: 16px;
  color: #979BA5;
  cursor: pointer;
}

.icon-hover:hover {
  color: #3a84ff;
}
</style>
