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
  <div>
    <article
      v-if="markdownHtml"
      class="doc-auth-section ag-markdown-view"
    >
      <header
        class="auth-header"
        @click="handleToggle"
      >
        <AgIcon
          name="down-shape"
          class="auth-toggle-icon"
          :class="{ fold: !isExpanded }"
        />
        <h3 id="doc-heading-认证方式">
          {{ t('认证方式') }}
        </h3>
        <!-- <BkLink
          v-if="authDocUrl"
          class="auth-doc-link"
          theme="primary"
          :href="authDocUrl"
          target="_blank"
          @click.stop
          >
          {{ t('查看文档') }}
          <AgIcon
          name="jump"
          size="12"
          class="auth-doc-link-icon"
          />
          </BkLink> -->
      </header>
      <div
        v-show="isExpanded"
        v-bk-xss-html="markdownHtml"
        class="auth-body"
      />
    </article>
  </div>
</template>

<script lang="ts" setup>

interface IProps {
  // 认证说明 markdown 渲染后的 html
  markdownHtml?: string
}

const { markdownHtml = '' } = defineProps<IProps>();

const { t } = useI18n();

const isExpanded = ref(false);

// 认证方式查看详情入口
// const authDocUrl = computed(() => envStore.env?.DOC_LINKS?.AUTH);

const handleToggle = () => {
  isExpanded.value = !isExpanded.value;
};

// 切换资源、环境后重新折叠
watch(() => markdownHtml, () => {
  isExpanded.value = false;
});
</script>

<style scoped lang="scss">
.doc-auth-section {
  margin-bottom: 24px;

  .auth-header {
    display: flex;
    align-items: center;
    margin-bottom: 0;
    cursor: pointer;

    h3 {
      margin: 0 !important;
      font-size: 16px;
      font-weight: 700;
      line-height: 22px;
    }
  }

  .auth-toggle-icon {
    flex-shrink: 0;
    margin-right: 8px;
    font-size: 12px;
    color: #979ba5;
    transition: transform .2s;

    &.fold {
      transform: rotate(-90deg);
    }
  }

  .auth-doc-link {
    display: inline-flex;
    align-items: center;
    margin-left: 8px;
    font-size: 14px;
    line-height: 22px;
  }

  .auth-doc-link-icon {
    margin-left: 4px;
  }

  .auth-body {
    margin-top: 12px;
  }
}
</style>
