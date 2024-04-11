<template>
  <bk-popover
    placement="bottom"
    theme="light"
    :arrow="false"
    :padding="0"
    :always="false"
  >
    <div class="info-icon">
      <span class="icon apigateway-icon icon-ag-help-document-fill"></span>
    </div>
    <template #content>
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
    <ReleaseNote
      v-model:show="showSyncReleaseNote"
      :list="syncReleaseList"
      :detail="releaseNoteDetail"
      :loading="syncReleaseNoteLoading"
      @selected="handleSelectRelease" />
  </bk-popover>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import semver from 'semver';
import ReleaseNote from '@blueking/release-note';
import '@blueking/release-note/dist/vue3-light.css';

import { useGetGlobalProperties } from '@/hooks';
import { getVersionLog } from '@/http';

const { t } = useI18n();

const globalProperties = useGetGlobalProperties();
const { GLOBAL_CONFIG } = globalProperties;

const showVersionLog = () => {
  showSyncReleaseNote.value = true;
};

const showSyncReleaseNote = ref(false);
const syncReleaseNoteLoading = ref(false);
const releaseNoteDetail = ref('');

const handleSelectRelease = (version: any) => {
  syncReleaseNoteLoading.value = true;
  setTimeout(() => {
    releaseNoteDetail.value = version.content;
    syncReleaseNoteLoading.value = false;
  }, 500);
};

const syncReleaseList = ref([]);

onMounted(async () => {
  const list = await getVersionLog();
  list.forEach((item: any) => {
    syncReleaseList.value.push({
      title: item.version,
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
  cursor: pointer;
  margin-right: 30px;
}
.info-icon:hover {
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
