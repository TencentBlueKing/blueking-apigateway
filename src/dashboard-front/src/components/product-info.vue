<template>
  <bk-popover
    placement="bottom"
    theme="light"
    :arrow="false"
    :padding="0"
    :always="false"
  >
    <div class="info-icon">
      <span class="icon apigateway-icon icon-ag-help-document-fill f18"></span>
    </div>
    <template #content>
      <bk-link class="info-item" :href="GLOBAL_CONFIG.DOC.GUIDE" target="_blank">
        {{ t('产品文档') }}
      </bk-link>
      <span text class="info-item" @click="showVersionLog">
        {{ t('版本日志') }}
      </span>
      <bk-link
        class="info-item" :href="GLOBAL_CONFIG.HELPER.href" target="_blank"
        v-if="GLOBAL_CONFIG.HELPER.href && GLOBAL_CONFIG.HELPER.name">
        {{ t(GLOBAL_CONFIG.HELPER.name) }}
      </bk-link>
      <!-- v-if="GLOBAL_CONFIG.BK_FEED_BACK_LINK" -->
      <bk-link class="info-item" :href="GLOBAL_CONFIG.BK_FEED_BACK_LINK" target="_blank">
        {{ t('问题反馈') }}
      </bk-link>
      <!-- v-if="GLOBAL_CONFIG.MARKER" -->
      <bk-link class="info-item" :href="GLOBAL_CONFIG.MARKER" target="_blank">
        {{ t('开源社区') }}
      </bk-link>
    </template>
    <ReleaseNote v-model:show="showSyncReleaseNote" :list="syncReleaseList" />
  </bk-popover>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import semver from 'semver';
import ReleaseNote from '@blueking/release-note';
import '@blueking/release-note/vue3/vue3.css';

import { useGetGlobalProperties } from '@/hooks';
import { getVersionLog } from '@/http';

const { t } = useI18n();

const globalProperties = useGetGlobalProperties();
const { GLOBAL_CONFIG } = globalProperties;

const showVersionLog = () => {
  showSyncReleaseNote.value = true;
};

const showSyncReleaseNote = ref(false);
const syncReleaseList = ref([]);

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
  if (!localLatestVersion
    || semver.compare(localLatestVersion.replace(/^V/, ''), latestVersion.replace(/^V/, '')) === -1
  ) {
    localStorage.setItem('latest-version', latestVersion);
    showVersionLog();
  }
});

</script>

<style lang="scss" scoped>
.info-icon {
  width: 32px;
  height: 32px;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 50%;
  cursor: pointer;
}
.info-icon:hover {
  background-color: #303d55;
  color: #fff;
}
.info-item {
  display: block;
  color: #63656E;
  padding: 8px 15px;
  margin-top: 5px;
  font-size: 12px;
  user-select: none;
  cursor: pointer;
  &:hover {
    color: #979ba5;
  }
}
.info-item:hover {
  background: #f3f6f9;
}
.info-item:nth-of-type(1) {
    margin-top: 0px;
}
</style>
