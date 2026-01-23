<template>
  <div class="collapse">
    <div class="header">
      <div
        v-bk-tooltips="{content: t('当前只有一个后端服务地址，存在多个后端服务地址才可以配置健康检查'), disabled: !disabled}"
        class="prefix"
      >
        <BkCheckbox
          v-model="enabled"
          :disabled="disabled"
          @change="handleCheckboxChanged"
        />
      </div>
      <div
        class="title"
        @click="handleTitleClicked"
      >
        <div class="name">
          {{ name }}
        </div>
        <div class="desc">
          <BkOverflowTitle
            resizeable
            type="tips"
          >
            {{ desc }}
          </BkOverflowTitle>
        </div>
      </div>
      <div
        class="suffix transition-transform"
        :class="{ '-rotate-180': !collapsed }"
      >
        <AgIcon
          name="down-shape"
          color="#979BA5"
          size="10"
        />
      </div>
    </div>
    <div
      v-show="!collapsed"
      class="content"
    >
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">

interface IProps {
  name?: string
  desc?: string
  disabled?: boolean
}

const enabled = defineModel<boolean>({ default: false });

const collapsed = defineModel<boolean>('collapsed', { default: true });

const {
  name = '',
  desc = '',
  disabled = false,
} = defineProps<IProps>();

const { t } = useI18n();

watch(() => disabled, () => {
  if (disabled) {
    collapsed.value = true;
  }
});

const handleCheckboxChanged = (checked: boolean) => {
  collapsed.value = !checked;
};

const handleTitleClicked = () => {
  if (disabled) {
    collapsed.value = true;
    return;
  }
  collapsed.value = !collapsed.value;
};

</script>

<style scoped lang="scss">
.collapse {
  width: 100%;

  .header {
    display: flex;
    height: 40px;
    padding-left: 8px;
    background: #FAFBFD;
    border: 1px solid #DCDEE5;
    border-radius: 2px;
    align-items: center;

    .prefix {
      display: flex;
      align-items: center;
      justify-content: center;
      padding-right: 8px;
    }

    .title {
      display: flex;
      align-items: center;
      width: calc(100% - 50px);
      cursor: pointer;

      .name {
        margin-right: 12px;
        font-size: 14px;
        font-weight: 700;
        line-height: 20px;
        color: #4D4F56;
        flex-shrink: 0;
      }

      .desc {
         width: calc(100% - 68px);
        font-size: 12px;
        line-height: 20px;
        color: #4D4F56;
      }
    }

    .suffix {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 8px;
      margin-left: auto;
    }
  }

  .content {
    padding: 16px 32px;
    background-color: #fff;
    border: 1px solid #DCDEE5;
    border-top: none;
    border-radius: 2px;
  }
}

</style>
