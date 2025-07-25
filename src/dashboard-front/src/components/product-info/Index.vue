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
        @click="showVersionLog"
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
    <ReleaseNote
      v-model:show="showSyncReleaseNote"
      :list="syncReleaseList"
    />
  </BkPopover>
</template>

<script setup lang="ts">
import semver from 'semver';
import ReleaseNote from '@blueking/release-note';
import '@blueking/release-note/vue3/vue3.css';

import { getVersionLog } from '@/services/source/basic';
import { useEnv } from '@/stores';

const { t } = useI18n();
const envStore = useEnv();

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
