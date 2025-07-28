/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */

<template>
  <div class="query-log">
    <div class="page-header">
      <BkInput
        v-model.trim="requestId"
        class="header-input"
        clearable
        :placeholder="t('请输入 request_id 进行查询')"
        @enter="getDetailData"
        @clear="handleClear"
      />

      <BkButton
        theme="primary"
        @click="getDetailData"
      >
        {{ t('查询') }}
      </BkButton>
    </div>

    <div class="query-log-body">
      <div class="body-header">
        <div class="body-title">
          {{ t('查询结果') }}
        </div>

        <div class="body-copy-btn">
          <BkButton
            v-show="!isEmpty"
            theme="primary"
            text
            @click="() => handleClickCopyLink(details.result)"
          >
            <AgIcon
              class="icon"
              name="copy-shape"
            />
            <span class="copy-text">
              {{ t('复制日志链接') }}
            </span>
          </BkButton>
        </div>
      </div>

      <BkLoading
        :loading="isDataLoading"
        color="#fafbfd"
        :opacity="1"
      >
        <div
          v-show="!isEmpty"
          class="body-content"
        >
          <dl class="details">
            <div
              v-for="({ label, field }, index) in details.fields"
              :key="index"
              class="item"
            >
              <dt class="label">
                {{ label }}
                <span class="fields">
                  ( <span
                    v-bk-tooltips="t('复制')"
                    class="fields-main"
                    @click.stop="copyToClipboard(field)"
                  >
                    {{ field }}
                  </span> ) :
                </span>
              </dt>
              <dd class="value">
                <span
                  v-if="field === 'response_body' && details.result?.status === '200'"
                  class="respond"
                >
                  <!-- <info-line class="respond-icon" /> -->
                  <span>{{ t('状态码为 200 时不记录响应正文') }}</span>
                </span>
                <span v-else>
                  {{ formatValue(details.result[field], field) }}
                </span>

                <span
                  v-if="details.result[field]"
                  class="opt-btns"
                >
                  <AgIcon
                    v-bk-tooltips="t('复制')"
                    class="opt-copy"
                    name="copy-shape"
                    @click="() => handleRowCopy(field, details.result)"
                  />
                </span>
              </dd>
            </div>
          </dl>
        </div>

        <div
          v-show="isEmpty"
          class="empty-wrapper"
        >
          <TableEmpty
            :empty-type="tableEmptyConf.emptyType"
            :abnormal="tableEmptyConf.isAbnormal"
            @refresh="refreshData"
            @clear-filter="refreshData"
          />
        </div>
      </BkLoading>
    </div>
  </div>
</template>

<script lang="ts" setup>
import AgIcon from '@/components/ag-icon/Index.vue';
import { Message } from 'bkui-vue';
import { copy as copyToClipboard } from '@/utils';
import TableEmpty from '@/components/table-empty/Index.vue';
import { getLogsInfo } from '@/services/source/access-log';
import dayjs from 'dayjs';

const route = useRoute();
const { t } = useI18n();

const isDataLoading = ref<boolean>(false);
const requestId = ref<string>('');
const details = ref<any>({
  fields: [],
  result: {},
});
const tableEmptyConf = ref<{
  emptyType: string
  isAbnormal: boolean
}>({
  emptyType: '',
  isAbnormal: false,
});

const isEmpty = computed(() => {
  return !Object.keys(details.value.result)?.length;
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
  updateTableEmptyConfig();
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
  }
  catch (e) {
    const error = e as Error;
    Message({
      theme: 'error',
      message: error.message,
    });
    details.value = {
      fields: [],
      result: {},
    };
  }
  finally {
    isDataLoading.value = false;
    updateTableEmptyConfig();
  }
};

const refreshData = () => {
  handleClear();
};

const updateTableEmptyConfig = () => {
  if (requestId.value) {
    tableEmptyConf.value.emptyType = 'searchEmpty';
    return;
  }
  tableEmptyConf.value.emptyType = '';
};

const formatValue = (value, field: string) => {
  if (value && ['timestamp'].includes(field)) {
    return dayjs.unix(value).format('YYYY-MM-DD HH:mm:ss ZZ');
  }
  return value || '--';
};

const handleRowCopy = (field: string, row) => {
  const copyStr = `${field}: ${row[field]}`;
  copyToClipboard(copyStr);
};

const handleClickCopyLink = ({ request_id }) => {
  if (!request_id) {
    return;
  }

  try {
    const link = `${window.location.href}/?request_id=${request_id}`;
    copyToClipboard(link || '');
  }
  catch (e) {
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
