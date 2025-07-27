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
 * 读取文件内容
 * @param {Object} file file文件对象
 */
export const getStrFromFile = (file: any) => {
  let resolveFn = (value: unknown) => {
  };
  const PromiseFunc = new Promise(resolve => resolveFn = resolve);
  // ▼ new 一个 FileReader
  // ▼ 然后监听 onload 事件，从中取得文本内容
  const oReader = Object.assign(new FileReader(), {
    onload(event: any) {
      resolveFn(event.target.result);
    },
  });
  oReader.readAsText(file);
  return PromiseFunc;
};

export const is24HoursAgo = (dateString: string) => {
  // 将日期字符串转换为 Date 对象
  const date: any = new Date(dateString);

  // 获取当前时间
  const now: any = new Date();

  // 计算时间差，单位为毫秒
  const diff = now - date;

  // 将时间差转换为小时
  const hours = diff / (1000 * 60 * 60);

  // 判断时间差是否大于等于24小时
  return hours >= 24;
};
