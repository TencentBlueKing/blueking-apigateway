<template>
  <!--  sdk语言选择器  -->
  <div class="lang-selector-wrap bk-button-group">
    <BkButton
      v-for="lang in langList"
      :key="lang"
      v-bk-tooltips="{ content: getTooltipContent(lang), disabled: isSdkGenerated(lang) }"
      :class="{ 'is-selected': lang === language }"
      :disabled="!isSdkGenerated(lang)"
      :style="{
        width: `${width}px`,
        'margin-bottom': `${marginBottom}px`,
      }"
      @click="() => handleSelect(lang)"
    >
      {{ useChangeCase(lang, 'capitalCase') }}
    </BkButton>
  </div>
</template>

<script setup lang="ts">
import { useChangeCase } from '@vueuse/integrations/useChangeCase';
import { type LanguageType } from '../types';

interface IProps {
  width: number
  marginBottom: number
  sdkLanguages: LanguageType[]
  langList: LanguageType[]
  maintainers: string[]
}

const language = defineModel<LanguageType>({ default: 'python' });

const {
  width = 150, // 按钮宽度
  marginBottom = 24,
  // 文档包含的sdk语言列表
  sdkLanguages = [
    'python',
    'java',
  ],
  // 可供选择的语言列表
  langList = [
    'python',
    'java',
    'golang',
  ],
  maintainers = [],
} = defineProps<IProps>();

const emit = defineEmits<{ select: [language: LanguageType] }>();

const { t } = useI18n();

const getTooltipContent = (lang: string) => {
  if (maintainers.length) {
    return t('{lang} SDK未生成，可联系负责人生成SDK：{maintainers}', {
      lang,
      maintainers: maintainers.join(','),
    });
  }
  return t('{lang} SDK未生成，可联系负责人生成SDK', { lang });
};

// 检查是否已生成该语言的sdk
const isSdkGenerated = (lang: LanguageType) => {
  return sdkLanguages.includes(lang);
};

const handleSelect = (lang: LanguageType) => {
  language.value = lang;
  emit('select', language.value);
};

</script>
