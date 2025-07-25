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
 * 导出下载公共方法
 * @param {Object} res 接口返回值
 */
export const blobDownLoad = async (res: any) => {
  if (res.ok) {
    const blob: any = await res.blob();
    const disposition = res.headers.get('Content-Disposition') || '';
    const url = URL.createObjectURL(blob);
    const elment = document.createElement('a');

    elment.download = (disposition.match(/filename="(\S+?)"/) || [])[1];
    elment.href = url;
    elment.click();
    URL.revokeObjectURL(blob);
    return Promise.resolve({ success: true });
  }

  const errorInfo = await res.json();
  return Promise.reject(errorInfo);
};
