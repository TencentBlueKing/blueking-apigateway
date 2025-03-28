<template>
  <div class="query-log">
    <div class="page-header">
      <bk-input
        class="header-input"
        v-model.trim="requestId"
        clearable
        type="search"
        @enter="getDetailData"
        @clear="handleClear"
      />

      <bk-button
        theme="primary"
        @click="getDetailData"
      >
        {{ t('查询') }}
      </bk-button>
    </div>

    <div class="query-log-body">
      <div class="body-header">
        <div class="body-title">
          {{ t('查询结果') }}
        </div>

        <div class="body-copy-btn">
          <bk-button
            theme="primary"
            text
            @click="handleClickCopyLink(details.result)"
          >
            <copy-shape />
            <span class="copy-text">
              {{ t('复制日志链接') }}
            </span>
          </bk-button>
        </div>
      </div>

      <bk-loading :loading="isDataLoading" color="#fafbfd" :opacity="1">

        <div class="body-content" v-show="!!details.fields?.length">
          <dl class="details">
            <div
              class="item"
              v-for="({ label, field }, index) in details.fields"
              :key="index">
              <dt class="label">
                {{ label }}
                <span class="fields">
                  ( <span
                    class="fields-main"
                    v-bk-tooltips="t('复制')"
                    @click.stop="copyToClipboard(field)">
                    {{ field }}
                  </span> ) :
                </span>
              </dt>
              <dd class="value">

                <span class="respond" v-if="field === 'response_body' && details.result?.status === '200'">
                  <info-line class="respond-icon" /><span>{{ t('状态码为 200 时不记录响应正文') }}</span>
                </span>
                <span v-else>
                  {{ formatValue(details.result[field], field) }}
                </span>

                <span class="opt-btns" v-if="details.result[field]">
                  <copy-shape v-bk-tooltips="t('复制')" @click="handleRowCopy(field, details.result)" class="opt-copy" />
                </span>

              </dd>
            </div>
          </dl>
        </div>

        <div class="empty-wrapper" v-show="!details.fields?.length">
          <bk-exception
            class="exception-part"
            :title="t('暂无数据')"
            :description="t('请先输入 request_id 进行查询')"
            scene="part"
            type="empty"
          />
        </div>
      </bk-loading>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { CopyShape } from 'bkui-vue/lib/icon';
import { Message } from 'bkui-vue';
import { copy as copyToClipboard } from '@/common/util';
import { getLogsInfo } from '@/http';
import dayjs from 'dayjs';

const route = useRoute();
const { t } = useI18n();

const isDataLoading = ref<boolean>(false);
const requestId = ref<string>('');
const details = ref<any>({
  fields: [],
  result: {},
});

onMounted(() => {
  init();
});

const init = () => {
  const id = route.query.request_id as string;

  if (id) {
    requestId.value = id;
    getDetailData();
  }
};

const handleClear = () => {
  requestId.value = '';
  details.value = {
    fields: [],
    result: {},
  };
};

const getDetailData = async () => {
  if (!requestId.value) {
    handleClear();
    return;
  }

  isDataLoading.value = true;

  try {
    const res = await getLogsInfo(requestId.value);
    details.value.result = res.results[0] || {};
    details.value.fields = res.fields;
  } catch (e) {
    const error = e as Error;
    Message({
      theme: 'error',
      message: error.message,
    });
    details.value = {
      fields: [],
      result: {},
    };
  } finally {
    isDataLoading.value = false;
  }
};

const formatValue = (value: any, field: string) => {
  if (value && ['timestamp'].includes(field)) {
    return dayjs.unix(value).format('YYYY-MM-DD HH:mm:ss ZZ');
  }
  return value || '--';
};

const handleRowCopy = (field:  string, row: any) => {
  const copyStr = `${field}: ${row[field]}`;
  copyToClipboard(copyStr);
};

const handleClickCopyLink = ({ request_id }: any) => {
  if (!request_id) {
    return;
  }

  try {
    const link = `${window.location.href}/?request_id=${request_id}`;
    copyToClipboard(link || '');
  } catch (e) {
    console.error(e);
  }
};

</script>

<style lang="scss" scoped>
.query-log {
  padding-top: 36px;
  .page-header {
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 24px;
    .header-input {
      width: 640px;
      margin-right: 8px;
    }
  }

  .query-log-body {
    padding: 0 76px 26px 68px;
    .body-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 12px;
      .body-title {
        font-weight: Bold;
        font-size: 14px;
        color: #4D4F56;
        line-height: 22px;
      }
      .body-copy-btn {
        font-size: 12px;
        .copy-text {
          margin-left: 2px;
        }
      }
    }
    .body-content {
      height: calc(100vh - 276px);
      padding: 24px;
      overflow-y: auto;
      box-sizing: border-box;
      border: 1px solid #DCDEE5;
    }
  }

  .empty-wrapper {
    padding-top: 126px;
    .exception-part {
      :deep(.bk-exception-img) {
        width: 220px;
        height: 112px;
      }
      :deep(.bk-exception-title) {
        font-size: 14px;
        color: #4D4F56;
        margin-top: -8px;
      }
      :deep(.bk-exception-description) {
        font-size: 12px;
        color: #979BA5;
      }
    }
  }
}

.details {
  position: relative;
  font-size: 12px;
  background-color: #ffffff;
  .item {
    display: flex;
    align-items: center;
    margin-bottom: 8px;

    .label {
      font-size: 12px;
      position: relative;
      flex: none;
      width: 212px;
      color: #63656E;
      margin-right: 12px;
      text-align: right;
      .fields {
        color: #979BA5;
        .fields-main {
          cursor: pointer;
          &:hover {
            background-color: #f0f1f5;
          }
        }
      }

      .copy-btn {
        color: #c4c6cc;
        font-size: 12px;
        position: absolute;
        right: -18px;
        top: 4px;
        cursor: pointer;

        &:hover {
          color: #3a84ff;
        }
      }
    }

    .value {
      font-family: "Courier New", Courier, monospace;
      flex: none;
      width: calc(100% - 400px);
      white-space: pre-wrap;
      word-break: break-word;
      color: #313238;
      line-height: 20px;
      display: flex;
      align-items: center;

      .respond {
        font-size: 12px;
        color: #FF9C01;
        display: flex;
        align-items: center;
        .respond-icon {
          margin-right: 4px;
          margin-top: -2px;
        }
      }

      .opt-btns {
        color: #979BA5;
        font-size: 16px;
        padding-top: 3px;
        margin-left: 10px;
        &:hover {
          color: #1768EF;
        }
        .opt-copy {
          font-size: 14px;
        }
        span {
          cursor: pointer;
          margin-right: -4px;
        }
      }
    }
  }
}
</style>
