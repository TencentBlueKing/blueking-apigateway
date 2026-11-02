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

import { createI18n } from 'vue-i18n';
import cn from './cn.json';
import en from './en.json';
import Cookie from 'js-cookie';

// 蓝鲸体系下 blueking_language 可能是 EN / en-US 等变体，直接当 locale 会与注册的 'en' 键不匹配，
const normalizeLocale = (raw?: string) => (raw || '').toLowerCase().startsWith('en') ? 'en' : 'zh-cn';

const cookieLocale = normalizeLocale(Cookie.get('blueking_language'));

const i18n = createI18n({
  legacy: false,
  locale: cookieLocale,
  fallbackLocale: 'zh-cn',
  // 部分词条（如删除确认的 <code> 高亮）按设计包含 HTML，
  // 渲染处统一通过 v-bk-xss-html 过滤，这里关闭开发期的 HTML 提示
  warnHtmlMessage: false,
  messages: {
    'zh-cn': cn,
    'en': en,
  },
});
export const { t, locale } = i18n.global;

export default i18n;
