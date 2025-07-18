/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
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
/**
 * @desc 正则表达式关键字符转换
 * @param { String } paramStr
 * @returns { String }
 */
export const encodeRegexp = (paramStr: string) => {
  const regexpKeyword = ['\\', '.', '*', '-', '{', '}', '[', ']', '^', '(', ')', '$', '+', '?', '|'];
  const res = regexpKeyword.reduce(
    (result, charItem) => result.replace(new RegExp(`\\${charItem}`, 'g'), `\\${charItem}`),
    paramStr,
  );
  return res;
};

/**
 * @desc 多行文本处理
 * @param { String } text
 * @returns { String }
 */
export const encodeMult = (text: string) => {
  const temp = document.createElement('textarea');
  temp.value = text;
  return temp.value;
};

/**
 * @desc 格式化用户输入的HTML
 * @param { String } str
 * @returns { String }
 */
export const escapeHTML = (str: string) =>
  str.replace(/&/g, '&#38;').replace(/"/g, '&#34;').replace(/'/g, '&#39;').replace(/</g, '&#60;');

/**
 * 转换角色为通用角色名
 * @param { String } str
 * @returns { String }
 */
export const switchToNormalRole = (str: string) => {
  if (str === 'redis_slave') {
    return 'slave';
  }
  if (str === 'redis_master') {
    return 'master';
  }
  return 'proxy';
};
