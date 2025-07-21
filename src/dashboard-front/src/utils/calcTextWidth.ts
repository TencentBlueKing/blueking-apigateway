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
export const calcTextWidth = (text: string, parentEl = document.body) => {
  const $el = document.createElement('div');
  $el.innerText = text;
  $el.style.position = 'absolute';
  $el.style.width = 'auto';
  $el.style.opacity = '0';
  $el.style.zIndex = '-1';
  $el.style.whiteSpace = 'pre';
  $el.style.wordBreak = 'no-break';
  parentEl.appendChild($el);
  const { width } = $el.getBoundingClientRect();
  parentEl.removeChild($el);

  return width;
};

export const calcTextHeight = (text: string, width: number, lineHeight = 40, parentEl = document.body) => {
  const $el = document.createElement('div');
  $el.innerText = text;
  $el.style.position = 'absolute';
  $el.style.width = `${width}px`;
  $el.style.opacity = '0';
  $el.style.zIndex = '-1';
  $el.style.whiteSpace = 'pre-wrap';
  $el.style.lineHeight = `${lineHeight}px`;
  parentEl.appendChild($el);
  const { height } = $el.getBoundingClientRect();
  parentEl.removeChild($el);

  return height;
};
