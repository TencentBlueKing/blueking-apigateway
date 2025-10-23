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
  <!--  查看 SDK 弹窗  -->
  <BkDialog
    v-model:is-show="isShow"
    :title="title"
    class="custom-main-dialog"
    width="640"
    mask-close
  >
    <main class="dialog-content">
      <div class="dialog-main">
        <LangSelector
          v-model="language"
          :sdk-languages="sdks.map(item => item.language)"
          :lang-list="languages"
          :maintainers="maintainers"
        />
        <SdkDetail
          v-if="curSdk"
          :sdk="curSdk"
          is-apigw
        />
      </div>
    </main>
  </BkDialog>
</template>

<script setup lang="ts">
import LangSelector from './LangSelector.vue';
import type {
  ISdk,
  LanguageType,
} from '../types.d.ts';
import SdkDetail from './SDKDetail.vue';
import { useI18n } from 'vue-i18n';

interface IProps {
  sdks?: ISdk[]
  targetName?: string
  languages: LanguageType[] | undefined
  maintainers?: string[]
}

const isShow = defineModel<boolean>({
  required: true,
  default: false,
});

const {
  sdks = [],
  targetName = '',
  maintainers = [],
} = defineProps<IProps>();

const { t } = useI18n();

const language = ref<LanguageType>('python');

const curSdk = computed(() => {
  return sdks.find(item => item.language === language.value) ?? null;
});

const title = computed(() => {
  return targetName ? t('{name} SDK', { name: targetName }) : t('查看 SDK');
});

watchEffect(() => {
  language.value = sdks[0]?.language || 'python';
});

</script>

<style scoped lang="scss">
.custom-main-dialog {

  :deep(.bk-dialog-title) {
    line-height: 28px;
  }

  :deep(.bk-dialog-content) {
    padding-right: 8px;
    margin-top: 20px;
  }

  :deep(.bk-modal-footer) {
    display: none;
  }

  .dialog-content {

    .dialog-main {

      .data-box {
        padding: 24px 12px;
        background: #f5f7fa;

        .row-item {
          display: flex;
          line-height: 40px;

          .key {
            width: 100px;
            padding-right: 10px;
            text-align: right;
          }

          .value {
            color: #313238;
            white-space: nowrap;
            flex: 1;
          }
        }
      }
    }
  }
}
</style>
