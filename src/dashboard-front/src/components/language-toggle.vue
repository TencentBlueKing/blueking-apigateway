<template>
  <bk-popover
    theme="light" placement="bottom" :arrow="false" :padding="0">
    <div class="toggle-language-icon">
      <span
        class="icon apigateway-icon"
        :class="locale === 'en' ? 'icon-ag-toggle-english' : 'icon-ag-toggle-chinese'"></span>
    </div>
    <template #content>
      <div class="language-item" @click="toggleLanguage('chinese')">
        <span class="icon apigateway-icon icon-ag-toggle-chinese"></span>
        <span>中文</span>
      </div>
      <div class="language-item" @click="toggleLanguage('english')">
        <span class="icon apigateway-icon icon-ag-toggle-english"></span>
        <span>English</span>
      </div>
    </template>
  </bk-popover>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';

import { jsonpRequest } from '@/common/util';
// import { setLanguage } from '@/http';

const { locale } = useI18n();
const router = useRouter();

const toggleLanguage = async (idx: string) => {
  // locale.value = idx;
  // const data = new URLSearchParams();
  // data.append('language', idx === 'english' ? 'en' : 'zh-hans');
  // await setLanguage(data);
  // await setLanguage({
  //   language: idx === 'english' ? 'en' : 'zh-hans',
  // });

  console.error(`${window.BK_COMPONENT_API_URL}/api/c/compapi/v2/usermanage/fe_update_user_language/`);
  const res: any = await jsonpRequest(
    `${window.BK_COMPONENT_API_URL}/api/c/compapi/v2/usermanage/fe_update_user_language/`,
    {
      language: idx === 'english' ? 'en' : 'zh-cn',
    },
    'languageToggle',
  );
  if (res.code === 0) {
    router.go(0);
  }
};
</script>

<style lang="scss" scoped>
.toggle-language-icon {
  cursor: pointer;
  margin-right: 30px;
  .icon {
    font-size: 16px;
    vertical-align: middle;
  }
}
.toggle-language-icon:hover {
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
  margin-top: 0px;
}
</style>
