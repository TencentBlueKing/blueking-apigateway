<template>
  <div class="resource-searcher-wrapper">
    <BkSelect
      v-model="id"
      :filter-option="resourceFilterMethod"
      :list="list"
      :popover-options="{ boundary: 'parent', extCls: 'resource-dropdown-wrapper' }"
      :popover-width="180"
      class="resource-select"
      display-key="name"
      filterable
      id-key="id"
      input-search
      scroll-height="262"
      v-bind="$attrs"
    >
      <template
        v-if="needPrefix"
        #prefix
      >
        <div class="label">
          {{ t('资源') }}
        </div>
      </template>
      <template #optionRender="{ item } ">
        <div class="resource-option-wrapper">
          <strong v-dompurify-html="getHighlightContent(item, 'name')" />
          <span
            v-dompurify-html="getHighlightContent(item, 'path')"
            class="path"
          />
        </div>
      </template>
    </BkSelect>
  </div>
</template>

<script lang="ts" setup>
// import { ResourcesItem } from '@/views/resource/setting/types';

interface IProp {
  list?: any[]
  needPrefix?: boolean
}

const id = defineModel<string | number>();

const {
  list = [],
  needPrefix = true,
} = defineProps<IProp>();

const emit = defineEmits<{ change: [id: string | number] }>();

const { t } = useI18n();

const keyword = ref('');

const resourceFilterMethod = (searchValue: string, option: any) => {
  keyword.value = searchValue || '';
  const resource = list.find(item => item.name === option.name);
  return resource?.name.includes(searchValue) || resource?.path.includes(searchValue);
};

const getHighlightContent = (item, field) => {
  const value = item[field] as string;
  if (keyword.value) {
    return value.replace(new RegExp(`(${keyword.value})`), '<em class="keyword">$1</em>');
  }
  return value;
};

watch(id, () => {
  handleChange();
});

const handleChange = () => {
  emit('change', id.value);
};

</script>

<style lang="scss" scoped>
.resource-searcher-wrapper {

  .resource-select {

    .label {
      font-size: 12px;
      color: #63656e;
      padding: 0 8px;
      line-height: 30px;
      background: #fafbfd;
      border-right: 1px solid #c4c6cc;
    }
  }

  .resource-dropdown-wrapper {
    .bk-select-content-wrapper .bk-select-option {
      border: 1px solid red !important;
    }

    .bk-popover.bk-pop2-content.bk-select-popover .bk-select-content-wrapper .bk-select-option {
      border: 1px solid red !important;

    }

    .bk-select-option {
      height: 43px !important;

      .resource-option-wrapper {
        padding-block: 4px;
        width: 100%;
        display: flex;
        flex-direction: column;
        line-height: 20px;

        .path {
          font-size: 10px;
          line-height: 14px;
        }

        .keyword {
          color: #3a84ff !important;
        }
      }
    }
  }
}
</style>

<style lang="scss">

.resource-dropdown-wrapper {
  .bk-select-option {
    height: 43px !important;

    .resource-option-wrapper {
      padding-block: 4px;
      width: 100%;
      display: flex;
      flex-direction: column;
      line-height: 20px;

      .path {
        font-size: 10px;
        line-height: 14px;
      }

      .keyword {
        color: #3a84ff !important;
      }
    }
  }
}
</style>
