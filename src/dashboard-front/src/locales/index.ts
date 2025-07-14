import { createI18n } from 'vue-i18n';

const i18n = createI18n({
  legacy: false,
  locale: 'zh-cn',
  fallbackLocale: 'zh-cn',
  // TODO 暂时静默语言包缺失
  missing: () => {
  },
  messages: {
    'zh-cn': { message: { hello: '你好世界' } },
    'en': { message: { hello: 'hello world' } },
  },
});

export const { t, locale } = i18n.global;

export default i18n;
