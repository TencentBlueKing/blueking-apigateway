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

// 环境状态文本
export const getStatusText = (status: string) => {
  let text = '';
  switch (status) {
    case 'success':
      text = '已上线';
      break;
    case 'successful':
      text = '已上线';
      break;
    case 'failure':
      text = '发布失败';
      break;
    case 'fail':
      text = '发布失败';
      break;
    case 'failed':
      text = '发布失败';
      break;
    case 'unreleased':
      text = '未发布';
      break;
    case 'delist':
      text = '已下架';
      break;
  }
  return text;
};
