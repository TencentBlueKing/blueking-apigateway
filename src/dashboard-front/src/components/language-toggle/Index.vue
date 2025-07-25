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
  <bk-popover
    theme="light"
    placement="bottom"
    :arrow="false"
    :padding="0"
    disable-outside-click
  >
    <div class="toggle-language-icon">
      <AgIcon
        size="22"
        :name="locale === 'en' ? 'toggle-english' : 'toggle-chinese'"
      />
    </div>
    <template #content>
      <div
        class="language-item"
        @click="() => toggleLanguage('zh-cn')"
      >
        <AgIcon
          class="v-middle mr-4px"
          size="18"
          name="toggle-chinese"
        />
        <span>中文</span>
      </div>
      <div
        class="language-item"
        @click="() => toggleLanguage('en')"
      >
        <AgIcon
          class="v-middle mr-4px"
          size="18"
          name="toggle-english"
        />
        <span>English</span>
      </div>
    </template>
  </bk-popover>
</template>

<script setup lang="ts">
import Cookie from 'js-cookie';

const { locale } = useI18n();
const router = useRouter();

const toggleLanguage = async (lang: string) => {
  Cookie.set('blueking_language', lang, { domain: getDomain() });
  router.go(0);
};

const getDomain = () => {
  const { hostname } = window.location;
  if (hostname === 'localhost') {
    return hostname;
  }
  const nameArr = hostname.split('.');
  nameArr.shift();
  return `${nameArr.join('.')}`;
};

</script>

<style lang="scss" scoped>
.toggle-language-icon {
  display: flex;
  width: 32px;
  height: 32px;
  cursor: pointer;
  border-radius: 50%;
  justify-content: center;
  align-items: center;
}

.toggle-language-icon:hover {
  color: #fff;
  background-color: #303d55;
}

.language-item {
  display: flex;
  align-items: center;
  padding: 4px 12px;
  margin-top: 5px;
  font-size: 12px;
  color: #63656e;
  cursor: pointer;
}

.language-item:hover {
  background-color: #f3f6f9;
}

.language-item:nth-of-type(1) {
  margin-top: 0;
}
</style>
