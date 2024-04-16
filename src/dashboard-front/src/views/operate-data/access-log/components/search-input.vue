<template>
  <div ref="searchInputRef">
    <bk-input class="search-input" v-model="localValue" :placeholder="localPlaceholder" @enter="handleEnter">
      <template #suffix>
        <bk-button theme="primary" class="search-input-button" @click="handleSearch"> {{ t("搜索") }} </bk-button>
      </template>
    </bk-input>
  </div>
</template>

<script lang="ts" setup>
import { ref, watch } from 'vue';
import i18n from '@/language/i18n';
const { t } = i18n.global;

const props = defineProps({
  modeValue: {
    type: String,
    default: '',
  },
  placeholder: {
    type: String,
    default: '',
  },
});

const emit = defineEmits(['input', 'search']);

const searchInputRef = ref(null);
const localValue = ref('');
const localPlaceholder = ref('');
localPlaceholder.value = props.placeholder || t('请输入查询条件');

const handleEnter = () => {
  emit('search', localValue.value);
};

const handleSearch = () => {
  emit('search', localValue.value);
};

watch(
  () => props.modeValue,
  (payload: string) => {
    localValue.value = payload;
  },
);

watch(
  () => localValue.value,
  (payload: string) => {
    emit('input', payload);
  },
);

defineExpose({
  searchInputRef: searchInputRef.value,
});
</script>

<style lang="scss" scoped>
.search-input {
  border-bottom-right-radius: 0;
  border-top-right-radius: 0;
  border-right: 0;

  .search-input-button {
    height: auto;
    border: none;
    border-radius: 0;
  }
}
</style>
