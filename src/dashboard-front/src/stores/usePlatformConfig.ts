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
import { defineStore } from 'pinia';
import {
  type IPlatformConfig,
  type IPlatformConfigI18n,
  getI18nValue,
  getPlatformConfig,
  setDocumentTitle,
  setShortcutIcon,
} from '@blueking/platform-config';
import { locale } from '@/locales';
import { useEnv } from './useEnv';

interface IState { config: IPlatformConfig | null }

const DEFAULT_APP_CODE = 'bk_apigateway';

const I18N_KEYS: (keyof IPlatformConfigI18n)[] = [
  'name',
  'productName',
  'helperText',
  'brandImg',
  'brandName',
  'footerInfoHTML',
];

// 未配置 BK_SHARED_RES_URL 或远程配置拉取失败时使用的默认配置
const getDefaultConfig = (version: string): IPlatformConfig => ({
  bkAppCode: DEFAULT_APP_CODE,
  name: 'API Gateway',
  nameEn: 'API Gateway',
  brandName: '腾讯蓝鲸智云',
  brandNameEn: 'BlueKing',
  footerInfo: '[技术支持](https://wpa1.qq.com/KziXGWJs?_type=wpa&qidian=true) | [社区论坛](https://bk.tencent.com/s-mart/community/) | [产品官网](https://bk.tencent.com/index/)',
  footerInfoEn: '[Support](https://wpa1.qq.com/KziXGWJs?_type=wpa&qidian=true) | [Forum](https://bk.tencent.com/s-mart/community/) | [Official](https://bk.tencent.com/index/)',
  footerCopyright: `Copyright © 2012-${new Date().getFullYear()} Tencent BlueKing. All Rights Reserved. {{version}}`,
  version: version ? `V${version}` : '',
});

// 包内按 blueking_language cookie 原值判断语言，cookie 为 EN / en-US 等变体时会误判为中文，
// 这里按应用当前语言重新计算 i18n 字段，与页面其余文案保持一致
const localize = (config: IPlatformConfig): IPlatformConfig => {
  const lang = locale.value === 'en' ? 'en' : 'zh-cn';
  const i18n: IPlatformConfigI18n = {};
  I18N_KEYS.forEach((key) => {
    i18n[key] = getI18nValue(config, key, lang);
  });
  return {
    ...config,
    i18n,
  };
};

let pending: Promise<IPlatformConfig> | null = null;

export const usePlatformConfig = defineStore('usePlatformConfig', {
  state: (): IState => ({ config: null }),
  getters: {
    footerInfoHTML: state => state.config?.i18n?.footerInfoHTML ?? '',
    footerCopyright: state => state.config?.footerCopyrightContent ?? '',
  },
  actions: {
    /**
     * 拉取平台配置（全局只请求一次），并设置网页标题和 favicon
     * 远程地址依赖环境变量 BK_SHARED_RES_URL，需在环境变量加载完成后调用
     */
    fetchConfig() {
      if (!pending) {
        pending = this.loadConfig();
      }
      return pending;
    },
    async loadConfig() {
      const envStore = useEnv();
      const {
        BK_SHARED_RES_URL: sharedResUrl,
        BK_APP_CODE: appCode,
        BK_APIGATEWAY_VERSION: version,
      } = envStore.env;
      const defaults = getDefaultConfig(version);

      // 远程配置拉取失败时，getPlatformConfig 内部会回退到 defaults
      const config = sharedResUrl
        ? await getPlatformConfig(`${sharedResUrl.replace(/\/+$/, '')}/${appCode || DEFAULT_APP_CODE}/base.js`, defaults)
        : await getPlatformConfig(defaults);

      this.config = localize(config);
      if (this.config.favicon) {
        setShortcutIcon(this.config.favicon);
      }
      setDocumentTitle(this.config.i18n);
      return this.config;
    },
  },
});
