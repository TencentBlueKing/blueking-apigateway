<template>
  <bk-popover
    theme="light"
    placement="bottom"
    :arrow="false"
    :padding="0"
    disable-outside-click
  >
    <div class="toggle-language-icon">
      <span
        class="icon apigateway-icon f22"
        :class="locale === 'en' ? 'icon-ag-toggle-english' : 'icon-ag-toggle-chinese'"
      ></span>
    </div>
    <template #content>
      <div
        class="language-item"
        @click="toggleLanguage('chinese')"
      >
        <span class="icon apigateway-icon icon-ag-toggle-chinese"></span>
        <span>中文</span>
      </div>
      <div
        class="language-item"
        @click="toggleLanguage('english')"
      >
        <span class="icon apigateway-icon icon-ag-toggle-english"></span>
        <span>English</span>
      </div>
    </template>
  </bk-popover>
</template>

<script setup lang="ts">
import {
  ref,
  onMounted,
} from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import jsCookie from 'js-cookie';
import { jsonpRequest } from '@/common/util';
import { useSidebar } from '@/hooks';
import mitt from '@/common/event-bus';

const curLeavePageData = ref({});
const { initSidebarFormData, isSidebarClosed } = useSidebar();
const { locale } = useI18n();
const router = useRouter();

const toggleLanguage = async (idx: string) => {
  let result = true;
  if (Object.keys(curLeavePageData.value).length > 0) {
    result = await isSidebarClosed(JSON.stringify(curLeavePageData.value)) as boolean;
  }
  if (result) {
    curLeavePageData.value = {};
    const targetLanguage = idx === 'english' ? 'en' : 'zh-cn';
    const res: any = await jsonpRequest(
      `${window.BK_COMPONENT_API_URL}/api/c/compapi/v2/usermanage/fe_update_user_language/`,
      {
        language: targetLanguage,
      },
      'languageToggle',
    );
    if (res.code === 0) {
      jsCookie.set('blueking_language', targetLanguage, {
        domain: window.BK_DOMAIN,
        path: '/',
      });
      router.go(0);
    }
  }
};

onMounted(() => {
  mitt.on('on-leave-page-change', (payload: Record<string, any>) => {
    curLeavePageData.value = payload;
    initSidebarFormData(payload);
  });
});
</script>

<style lang="scss" scoped>
.toggle-language-icon {
  width: 32px;
  height: 32px;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 50%;
  cursor: pointer;

  .icon {
    font-size: 16px;
    vertical-align: middle;
  }
}

.toggle-language-icon:hover {
  background-color: #303d55;
  color: #fff;
}

.language-item {
  display: block;
  color: #63656e;
  padding: 4px 12px;
  margin-top: 5px;
  font-size: 12px;
  cursor: pointer;

  .icon {
    font-size: 18px;
    vertical-align: bottom;
  }
}

.language-item:hover {
  background-color: #f3f6f9;
}

.language-item:nth-of-type(1) {
  margin-top: 0;
}
</style>
