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
  <div class="card-wrapper">
    <header class="flex items-baseline justify-between card-header">
      <div class="flex items-baseline header-title-wrapper">
        <div class="header-title">
          <BkOverflowTitle
            type="tips"
            class="text-16px"
          >
            {{ server.title }}
          </BkOverflowTitle>
          <BkOverflowTitle
            type="tips"
            class="text-14px mt-12px"
          >
            {{ server.name }}
          </BkOverflowTitle>
        </div>
        <BkTag
          v-if="server.status === 1"
          size="small"
          theme="success"
        >
          {{ t('启用中') }}
        </BkTag>
        <BkTag
          v-else
          size="small"
        >
          {{ t('已停用') }}
        </BkTag>
      </div>
      <div class="header-actions">
        <div class="button-group">
          <BkButton
            :disabled="server.status === 0"
            size="small"
            theme="primary"
            @click.stop="handleEditClick"
          >
            {{ t('编辑') }}
          </BkButton>
          <BkButton
            v-if="server.status === 1"
            size="small"
            @click.stop="handleSuspendClick"
          >
            {{ t('停用') }}
          </BkButton>
          <BkButton
            v-else
            size="small"
            @click.stop="handleEnableClick"
          >
            {{ t('启用') }}
          </BkButton>
        </div>
        <div
          class="dropdown-wrapper"
          @click.stop="preventDefault"
        >
          <BkDropdown trigger="hover">
            <AgIcon
              class="dropdown-trigger"
              name="more-fill"
              size="16"
            />
            <template #content>
              <BkDropdownMenu>
                <!--                <BkDropdownItem @click="handleCloneClick"> -->
                <!--                  <BkButton text> -->
                <!--                    {{ t('克隆空间') }} -->
                <!--                  </BkButton> -->
                <!--                </BkDropdownItem> -->
                <BkDropdownItem>
                  <BkButton
                    v-bk-tooltips="{
                      content: t('请先停用再删除'),
                      disabled: server.status === 0,
                    }"
                    :disabled="server.status === 1"
                    text
                    @click="handleDeleteClick"
                  >
                    {{ t('删除') }}
                  </BkButton>
                </BkDropdownItem>
              </BkDropdownMenu>
            </template>
          </BkDropdown>
        </div>
      </div>
    </header>

    <!-- 分割线 -->
    <div class="divider" />

    <main class="card-main">
      <div class="main-content">
        <div class="content-item">
          <div class="item-label">
            {{ t('访问地址') }}:
          </div>
          <div
            v-bk-tooltips="server.url"
            class="item-value"
          >
            {{ server.url }}
          </div>
          <div class="item-suffix copy-btn">
            <AgIcon
              name="copy-info"
              @click.stop="() => copy(server.url)"
            />
          </div>
        </div>
        <div class="content-item">
          <div class="item-label">
            {{ t('环境') }}:
          </div>
          <div class="item-value">
            {{ server.stage.name }}
          </div>
        </div>
        <div class="content-item">
          <div class="item-label">
            {{ t('工具数量') }}:
          </div>
          <div class="item-value">
            {{ server.tools_count }}
          </div>
        </div>
        <div class="content-item">
          <div class="item-label">
            {{ t('标签') }}:
          </div>
          <div class="item-value">
            <template v-if="server.labels.length">
              <BkTag
                v-for="(label, index) in server.labels"
                :key="index"
                class="mr-8px"
                size="small"
              >
                {{ label }}
              </BkTag>
            </template>
            <span v-else>--</span>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script lang="ts" setup>
import { type IMCPServer } from '@/services/source/mcp-server';
import { copy } from '@/utils';

interface IProps { server: IMCPServer }

interface IEmits {
  edit: [id: number]
  suspend: [id: number]
  enable: [id: number]
  delete: [id: number]
}

const { server } = defineProps<IProps>();

const emit = defineEmits<IEmits>();

const { t } = useI18n();

const handleEditClick = () => {
  emit('edit', server.id);
};

const handleSuspendClick = () => {
  emit('suspend', server.id);
};

const handleEnableClick = () => {
  emit('enable', server.id);
};

const handleDeleteClick = () => {
  if (server.status === 1) {
    return;
  }
  emit('delete', server.id);
};

const preventDefault = (e: Event) => {
  e.preventDefault();
};

</script>

<style lang="scss" scoped>
.card-wrapper {
  // height: 228px;
  padding: 20px 40px;
  border-radius: 2px;
  background-color: #ffffff;
  box-shadow: 0 2px 4px 0 #1919290d;
  box-sizing: border-box;
  cursor: pointer;

  .card-header {

    .header-title-wrapper {
      max-width: calc(100% - 224px);

      .header-title {
        width: 100%;
        margin-right: 8px;
        font-size: 16px;
        font-weight: 700;
        line-height: 22px;
        color: #313238;
      }

      :deep(.bk-tag-text) {
        font-size: 12px !important;
      }
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 8px;

      .button-group {
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .dropdown-wrapper {

        .dropdown-trigger {
          display: flex;
          width: 26px;
          height: 26px;
          font-size: 16px;
          cursor: pointer;
          border-radius: 2px;
          justify-content: center;
          align-items: center;

          &:hover {
            background: #f0f1f5;
          }
        }
      }
    }
  }

  .divider {
    width: 453px;
    height: 1px;
    background: #eaebf0;
    margin-block: 18px 16px;
  }

  .card-main {

    .main-content {
      font-size: 12px;
      line-height: 32px;
      color: #313238;

      .content-item {
        display: flex;
        align-items: center;
        gap: 8px;

        .item-label {
          flex-shrink: 0;
        }

        .item-value {
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .item-suffix.copy-btn {
          cursor: pointer;

          &:hover {
            color: #3a84ff;
          }
        }
      }
    }
  }
}

@media (min-width: 768px) {
  .card-wrapper {
    width: calc(50% - 12px);
  }
}

@media (min-width: 1200px) {
  .card-wrapper {
    width: calc(33.333% - 16px);
  }
}
</style>
