import { createI18n } from 'vue-i18n';
import cookie from 'cookie';

import langMap from './lang';

interface ILANG_PKG {
  [propName: string]: string;
}

const en: ILANG_PKG = {};
const zh: ILANG_PKG = {};
Object.keys(langMap).forEach((key) => {
  en[key] = langMap[key][0] || key;
  zh[key] = langMap[key][1] || key;
});

// const language = (navigator.language || 'en').toLocaleLowerCase();
const localLanguage = cookie.parse(document.cookie).blueking_language || 'zh-hans';

const i18n = createI18n({
  silentTranslationWarn: true,
  legacy: false,
  locale: localLanguage,
  fallbackLocale: 'zh-hans',
  messages: {
    // 'zh-hans': Object.assign(lang.zhCN, zh),
    'zh-hans': zh,
    // en: Object.assign(lang.enUS, en),
    en,
  },
});

export const isChinese = localLanguage === 'zh-hans';

export default i18n;
