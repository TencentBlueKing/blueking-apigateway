/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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
  <div class="import-result-wrapper">
    <!--  导入中  -->
    <article
      v-if="status === 'loading'"
      class="content-wrap loading"
    >
      <main class="content-main">
        <BkLoading
          mode="spin"
          theme="primary"
          loading
        >
          <div class="w-full h-48px" />
        </BkLoading>
        <section class="title">
          {{ t('正在导入') }}
          <span class="font-bold">{{ addedCount + updatedCount }}</span>
          {{ t('个资源，请稍等...') }}
        </section>
      </main>
      <footer class="content-footer">
        <span>{{ t('新增了') }}
          <span
            class="font-bold color-#34d97b px-5px"
          >{{ addedCount }}</span>{{ t('个，更新') }}
          <span
            class="font-bold color-#ffb400 px-5px"
          >{{ updatedCount }}</span>{{ t('个资源') }}
        </span>
      </footer>
    </article>
    <!--  导入成功  -->
    <article
      v-else-if="status === 'success'"
      class="content-wrap success"
    >
      <main class="content-main">
        <Success
          width="64px"
          height="64px"
          fill="#2DCB56"
        />
        <section class="title">
          {{ t('成功导入') }}
          <span class="font-bold">{{ addedCount + updatedCount }}</span>
          {{ t('个资源') }}
        </section>
      </main>
      <footer class="content-footer">
        <span>{{ t('新增了') }}
          <span
            class="font-bold color-#34d97b px-5px"
          >{{ addedCount }}</span>{{ t('个，更新') }}
          <span
            class="font-bold color-#ffb400 px-5px"
          >{{ updatedCount }}</span>{{ t('个资源，为了后续导入方便，请及时下载最新的资源文件') }}
        </span>
        <span
          class="download-btn"
          @click="isResourceExportDialogShow = true"
        ><AgIcon
          name="download"
          class="btn-icon"
        />{{
          t('下载资源文件')
        }}</span>
        <span>{{ t('（包含所有资源）') }}</span>
      </footer>
      <section class="actions">
        <BkButton
          theme="primary"
          @click="emit('go-back')"
        >
          {{
            t('返回查看')
          }}
        </BkButton>
      </section>
    </article>
    <!--  导入失败  -->
    <article
      v-else
      class="content-wrap fail"
    >
      <main class="content-main">
        <Close
          width="64px"
          height="64px"
          fill="#EA3636"
        />
        <section class="title">
          {{ t('资源导入失败') }}
        </section>
      </main>
      <section class="actions">
        <BkButton
          theme="primary"
          @click="emit('retry')"
        >
          {{
            t('失败重试')
          }}
        </BkButton>
        <BkButton @click="emit('edit')">
          {{
            t('返回修改配置')
          }}
        </BkButton>
      </section>
      <section
        v-if="errorMessage"
        class="error-msg"
      >
        <BkAlert
          theme="error"
          :title="errorMessage"
          closable
          class="w-800px"
        />
      </section>
    </article>
    <!--  下载 dialog  -->
    <ResourceExportDialog v-model="isResourceExportDialogShow" />
  </div>
</template>

<script setup lang="ts">
import { Close, Success } from 'bkui-vue/lib/icon';
import type { ImportResultStatus } from '../types';
import ResourceExportDialog from './ResourceExportDialog.vue';

interface IProps {
  status: ImportResultStatus
  addedCount: number
  updatedCount: number
  errorMessage: string
}

const { status, addedCount, updatedCount, errorMessage } = defineProps<IProps>();

const emit = defineEmits<{
  'go-back': []
  'retry': []
  'edit': []
}>();

const { t } = useI18n();
const isResourceExportDialogShow = ref(false);
</script>

<style scoped lang="scss">
.import-result-wrapper {
  display: flex;
  height: 400px;
  margin: 20px 24px;
  background-color: #FFF;
  box-shadow: 0 2px 4px 0 #1919290d;
  justify-content: center;
  align-items: center;

  .content-wrap {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;

    .content-main {
      display: flex;
      margin-bottom: 16px;
      flex-direction: column;
      align-items: center;
      gap: 40px;

      .title {
        font-size: 24px;
        line-height: 32px;
        color: #313238;
      }
    }

    .content-footer {
      color: #63656E;

      .download-btn {
        margin-left: 4px;
        color: #3A84F6;
        cursor: pointer;

        .btn-icon {
          font-size: 18px;
        }
      }
    }

    .actions {
      display: flex;
      margin-top: 28px;
      align-items: center;
      gap: 8px;
    }

    .error-msg {
      margin-top: 16px;
    }
  }
}
</style>
