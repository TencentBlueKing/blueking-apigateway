<template>
  <div class="data-box wrapper">
    <div class="row-item mb10">
      <div class="key">
        <span class="column-key"> {{ t('SDK包名称') }}: </span>
      </div>
      <div class="value">
        <span class="column-value" v-bk-overflow-tips>{{params.sdk_name || '--'}}</span>
      </div>
    </div>
    <div class="row-item mb10">
      <div class="key">
        <span class="column-key"> {{ t('SDK版本') }}: </span>
      </div>
      <div class="value">
        <span class="column-value" v-bk-overflow-tips>{{params.sdk_version_number || '--'}}</span>
      </div>
    </div>

    <div class="row-item mb10">
      <div class="key">
        <span class="column-key"> {{ t('SDK地址') }}: </span>
      </div>
      <div class="value">
        <bk-popover placement="top" width="600">
          <span class="column-value vm">{{params.sdk_download_url || '--'}}</span>
          <template #content>
            <div style="white-space: normal;word-break: break-all;">
              {{ params.sdk_download_url }}
            </div>
          </template>
        </bk-popover>
        <i
          class="doc-copy vm icon-hover apigateway-icon icon-ag-copy ag-doc-icon"
          v-if="params.sdk_download_url"
          v-bk-tooltips="t('复制')"
          :data-clipboard-text="params.sdk_download_url">
        </i>
        <i
          class="ag-doc-icon doc-download-line vm icon-hover apigateway-icon icon-ag-download-line"
          v-if="params.sdk_download_url"
          v-bk-tooltips="t('下载')"
          @click="handleDownload">
        </i>
      </div>
    </div>

    <div class="row-item mb10">
      <div class="key">
        <span class="column-key"> {{ t('安装') }}: </span>
      </div>
      <div class="value">
        <bk-popover placement="top" width="600">
          <span class="column-value vm">{{params.sdk_install_command || '--'}}</span>
          <template #content>
            <div style="white-space: normal;word-break: break-all;">
              {{ params.sdk_install_command }}
            </div>
          </template>
        </bk-popover>
        <i
          class="ag-doc-icon doc-copy vm icon-hover apigateway-icon icon-ag-copy"
          v-if="params.sdk_install_command"
          v-bk-tooltips="t('复制')"
          :data-clipboard-text="params.sdk_install_command">
        </i>
      </div>
    </div>

    <template v-if="isApigw">
      <div class="row-item mb10">
        <div class="key">
          <span class="column-key">
            {{ t('资源版本') }}
            <span v-bk-tooltips="t('该SDK关联的API资源版本')">
              <i class="bk-icon icon-question-circle-shape" style="cursor:"></i>
            </span>
            :
          </span>
        </div>
        <div class="value">
          <span
            class="column-value"
            v-bk-tooltips.top="{ content: params.resource_version_display, allowHTML: false }">
            {{params.resource_version_display || '--'}}
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
          <span class="column-value" v-bk-tooltips.top="stageText">{{stageText || '--'}}</span>
        </div>
      </div>
    </template>
  </div>
</template>

<script lang="ts" setup>
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const props = defineProps({
  isApigw: {
    type: Boolean,
    default: false,
  },
  params: {
    type: Object,
    default: () => {
      return {
        sdk_name: '',
        sdk_version_number: '',
        sdk_download_url: '',
        sdk_install_command: '',
      };
    },
  },
});

const stageText = computed(() => {
  let texts = [];
  if (props.params?.released_stages) {
    texts = props.params?.released_stages.map((item: any) => item.name);
  }

  return texts.join(', ');
});

const handleDownload = () => {
  if (props.params?.sdk_download_url) {
    window.open(props.params.sdk_download_url);
  }
};
</script>

<style lang="scss" scoped>
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
