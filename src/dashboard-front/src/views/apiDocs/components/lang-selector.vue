<template>
  <!--  sdk语言选择器  -->
  <div class="lang-selector-wrap bk-button-group">
    <bk-button
      v-for="lang in langList"
      :key="lang"
      :class="{ 'is-selected': lang === language }"
      :disabled="!isSdkGenerated(lang)"
      :style="{
        width: `${width}px`,
        'margin-bottom': `${marginBottom}px`,
      }"
      v-bk-tooltips="{ content: getTooltipContent(lang), disabled: isSdkGenerated(lang) }"
      @click="handleSelect(lang)"
    >
      {{ useChangeCase(lang, 'capitalCase') }}
    </bk-button>
  </div>
</template>

<script setup lang="ts">
import { toRefs } from 'vue';
import { useChangeCase } from '@vueuse/integrations/useChangeCase';
import { LanguageType } from '@/views/apiDocs/types';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const language = defineModel<LanguageType>({
  default: 'python',
});

interface IProps {
  width: number;
  marginBottom: number;
  sdkLanguages: LanguageType[],
  langList: LanguageType[],
  maintainers: string[];
}

const props = withDefaults(defineProps<IProps>(), {
  width: 150,  // 按钮宽度
  marginBottom: 24,
  // 文档包含的sdk语言列表
  sdkLanguages: () => [
    'python',
    'java',
  ],
  // 可供选择的语言列表
  langList: () => [
    'python',
    'java',
    'golang',
  ],
  maintainers: () => [],
});

const {
  width,
  marginBottom,
  sdkLanguages,
  langList,
} = toRefs(props);

const emit = defineEmits<{
  'select': [language: LanguageType]
}>();

const getTooltipContent = (lang: string) => {
  if (props.maintainers.length) {
    return t('{lang} SDK未生成，可联系负责人生成SDK：{maintainers}', { lang, maintainers: props.maintainers.join(',') });
  }
  return t('{lang} SDK未生成，可联系负责人生成SDK', { lang });
};

// 检查是否已生成该语言的sdk
const isSdkGenerated = (lang: LanguageType) => {
  return sdkLanguages.value.includes(lang);
};

const handleSelect = (lang: LanguageType) => {
  language.value = lang;
  emit('select', language.value);
};

</script>
