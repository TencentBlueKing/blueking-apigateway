<template>
  <div class="card-wrapper">
    <header class="card-header">
      <div class="header-title-wrapper">
        <span class="header-title">{{ server.name }}</span>
        <BkTag
          v-if="server.status === 1"
          size="small"
          theme="success"
        >{{ t('启用中') }}
        </BkTag>
        <BkTag
          v-else
          size="small"
        >{{ t('已停用') }}
        </BkTag>
      </div>
      <div class="header-actions">
        <div class="button-group">
          <BkButton
            :disabled="server.status === 0"
            size="small"
            theme="primary"
            @click="handleEditClick"
          >
            {{ t('编辑') }}
          </BkButton>
          <BkButton
            v-if="server.status === 1"
            size="small"
            @click="handleSuspendClick"
          >
            {{ t('停用') }}
          </BkButton>
          <BkButton
            v-else
            size="small"
            @click="handleEnableClick"
          >
            {{ t('启用') }}
          </BkButton>
        </div>
        <div class="dropdown-wrapper">
          <BkDropdown trigger="hover">
            <AgIcon
              class="dropdown-trigger"
              name="more-fill"
              size="16"
            />
            <template #content>
              <BkDropdownMenu>
                <!--                <BkDropdownItem @click="handleCloneClick">-->
                <!--                  <BkButton text>-->
                <!--                    {{ t('克隆空间') }}-->
                <!--                  </BkButton>-->
                <!--                </BkDropdownItem>-->
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
    <div class="divider"></div>

    <main class="card-main">
      <div class="main-content">
        <div class="content-item">
          <div class="item-label">{{ t('访问地址') }}:</div>
          <div v-bk-tooltips="server.url" class="item-value">{{ server.url }}</div>
          <div class="item-suffix copy-btn">
            <AgIcon name="copy-info" @click="() => copy(server.url)" />
          </div>
        </div>
        <div class="content-item">
          <div class="item-label">{{ t('环境') }}:</div>
          <div class="item-value">{{ server.stage.name }}</div>
        </div>
        <div class="content-item">
          <div class="item-label">{{ t('工具数量') }}:</div>
          <div class="item-value">{{ server.tools_count }}</div>
        </div>
        <div class="content-item">
          <div class="item-label">{{ t('标签') }}:</div>
          <div class="item-value">
            <BkTag v-for="(label, index) in server.labels" :key="index" class="mr8" size="small">{{ label }}</BkTag>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
<script lang="ts" setup>
import { useI18n } from 'vue-i18n';
import AgIcon from '@/components/ag-icon.vue';
import { IMCPServer } from '@/http/mcp-server';
import { copy } from '@/common/util';

interface IProps {
  server: IMCPServer,
}

interface IEmits {
  edit: [id: number],
  suspend: [id: number],
  enable: [id: number],
  delete: [id: number],
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

</script>
<style lang="scss" scoped>
.card-wrapper {
  width: 533px;
  height: 228px;
  background: #fff;
  box-shadow: 0 2px 4px 0 #1919290d;
  border-radius: 2px;
  padding: 20px 40px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .header-title-wrapper {
      .header-title {
        font-weight: 700;
        font-size: 16px;
        color: #313238;
        line-height: 22px;
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
      color: #313238;
      line-height: 32px;

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
</style>
