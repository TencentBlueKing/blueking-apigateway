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
  <BkPopover
    placement="bottom"
    theme="light"
    :arrow="false"
    :padding="0"
    :always="false"
    disable-outside-click
  >
    <div class="info-icon">
      <AgIcon
        name="help-document-fill"
        size="18"
      />
    </div>
    <template #content>
      <BkLink
        class="info-item"
        :href="envStore.env.DOC_LINKS.GUIDE"
        target="_blank"
      >
        {{ t('产品文档') }}
      </BkLink>
      <span
        text
        class="info-item"
        @click="showVersionLog()"
      >
        {{ t('版本日志') }}
      </span>
      <BkLink
        v-if="envStore.env.HELPER.href && envStore.env.HELPER.name"
        class="info-item"
        :href="envStore.env.HELPER.href"
        target="_blank"
      >
        {{ envStore.env.HELPER.name || 'Helper' }}
      </BkLink>
      <BkLink
        class="info-item"
        href="https://bk.tencent.com/s-mart/community/"
        target="_blank"
      >
        {{ t('问题反馈') }}
      </BkLink>
      <BkLink
        class="info-item"
        href="https://github.com/TencentBlueKing/blueking-apigateway"
        target="_blank"
      >
        {{ t('开源社区') }}
      </BkLink>
    </template>
    <component
      :is="ReleaseNote"
      v-if="ReleaseNote"
      v-model:show="showSyncReleaseNote"
      :list="syncReleaseList"
    />
  </BkPopover>
</template>

<script setup lang="ts">
import type { Component } from 'vue';
import semverCompare from 'semver/functions/compare';

import { getVersionLog } from '@/services/source/platform/version-log';
import { useEnv } from '@/stores';
import { messageError } from '@/utils';

const { t } = useI18n();
const envStore = useEnv();

// 版本日志组件约 26 KB（gzip），首次打开时再加载，不放进首屏
const ReleaseNote = shallowRef<Component | null>(null);
const showSyncReleaseNote = ref(false);
const syncReleaseList = ref<any[]>([]);

// Vite 可能跳过加载失败的样式请求。保留本页的加载结果，刷新后再尝试。
let releaseNoteLoad: Promise<boolean> | undefined;

const loadReleaseNote = async () => {
  try {
    const [module] = await Promise.all([
      import('@blueking/release-note'),
      import('@blueking/release-note/vue3/vue3.css'),
    ]);
    ReleaseNote.value = module.default;
    // 先以关闭状态挂载，让组件监听到 show 从 false 变为 true。
    await nextTick();
    return true;
  }
  catch (error) {
    console.error('版本日志组件加载失败', error);
    return false;
  }
};

const showVersionLog = async (notifyOnFailure = true) => {
  releaseNoteLoad ??= loadReleaseNote();
  if (!await releaseNoteLoad) {
    if (notifyOnFailure) {
      messageError(t('静态文件加载失败，请刷新页面重试'));
    }
    return false;
  }
  showSyncReleaseNote.value = true;
  return true;
};

onMounted(async () => {
  const list = await getVersionLog();
  list.forEach((item: any) => {
    syncReleaseList.value.push({
      title: item.version,
      detail: item.content,
      ...item,
    });
  });

  const latestVersion = list[0].version;
  const localLatestVersion = localStorage.getItem('latest-version');
  const hasNewVersion = !localLatestVersion
    || semverCompare(localLatestVersion.replace(/^V/, ''), latestVersion.replace(/^V/, '')) === -1;
  if (hasNewVersion && await showVersionLog(false)) {
    await nextTick();
    localStorage.setItem('latest-version', latestVersion);
  }
});

</script>

<style lang="scss" scoped>
.info-icon {
  display: flex;
  width: 32px;
  height: 32px;
  cursor: pointer;
  border-radius: 50%;
  justify-content: center;
  align-items: center;
}

.info-icon:hover {
  color: #fff;
  background-color: #303d55;
}

.info-item {
  display: block;
  padding: 8px 15px;
  margin-top: 5px;
  font-size: 12px;
  color: #63656E;
  cursor: pointer;
  user-select: none;

  &:hover {
    color: #979ba5;
  }
}

.info-item:hover {
  background: #f3f6f9;
}

.info-item:nth-of-type(1) {
  margin-top: 0;
}
</style>
