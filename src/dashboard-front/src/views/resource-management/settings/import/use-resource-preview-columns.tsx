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

import type { PrimaryTableProps } from '@blueking/tdesign-ui';
import { RESOURCE_TYPE_LIST } from '@/constants';
import { METHOD_THEMES } from '@/enums';
import type { ILocalImportedResource } from '@/types/resource';

type PreviewColumn = NonNullable<PrimaryTableProps<ILocalImportedResource>['columns']>[number];

interface IPreviewColumns {
  identity: PreviewColumn[]
  requestAndBackend: PreviewColumn[]
}

const getResourceTypeData = (kind?: ILocalImportedResource['kind']) => {
  return RESOURCE_TYPE_LIST.find(item => item.value === kind);
};

export const useResourcePreviewColumns = (getIsAiGateway: () => boolean, pathWidth?: number) => {
  const { t } = useI18n();
  const pathSizing = pathWidth === undefined
    ? { minWidth: 160 }
    : {
      width: pathWidth,
      minWidth: 160,
    };

  return computed<IPreviewColumns>(() => {
    const isAiGateway = getIsAiGateway();
    return {
      identity: [
        {
          title: t('资源名称'),
          colKey: 'name',
          fixed: 'left',
          width: 160,
          minWidth: 160,
          ellipsis: true,
        },
        ...(isAiGateway
          ? [{
            title: t('资源类型'),
            colKey: 'kind',
            minWidth: 100,
            ellipsis: true,
            cell: (h: unknown, { row }: { row: ILocalImportedResource }) => (
              <bk-tag theme={getResourceTypeData(row.kind)?.theme ?? 'default'}>
                {getResourceTypeData(row.kind)?.label ?? t('普通 API')}
              </bk-tag>
            ),
          }]
          : []),
      ],
      requestAndBackend: [
        {
          title: t('前端请求路径'),
          colKey: 'path',
          ...pathSizing,
          ellipsis: true,
          cell: (h: unknown, { row }: { row: ILocalImportedResource & { path_display?: string } }) => (
            <span>{row.match_subpath ? row.path_display : row.path}</span>
          ),
        },
        {
          title: t('前端请求方法'),
          colKey: 'method',
          cell: (h: unknown, { row }: { row: ILocalImportedResource }) => (
            <bk-tag theme={(METHOD_THEMES as any)[row.method!]}>
              {row.method}
            </bk-tag>
          ),
        },
        {
          title: isAiGateway ? t('后端/模型服务') : t('后端服务'),
          colKey: 'backend',
          ellipsis: true,
          cell: (h: unknown, { row }: { row: ILocalImportedResource }) => row.backend?.name ?? 'default',
        },
        ...(!isAiGateway
          ? [
            {
              title: t('后端请求方法'),
              colKey: 'backend_method',
              cell: (h: unknown, { row }: { row: ILocalImportedResource }) => {
                const method = row.backend?.config?.method ?? row.method;
                return <bk-tag theme={method && METHOD_THEMES[method]}>{method}</bk-tag>;
              },
            },
            {
              title: t('后端请求路径'),
              colKey: 'backend_path',
              ...pathSizing,
              ellipsis: true,
              cell: (h: unknown, { row }: { row: ILocalImportedResource }) => (
                row.backend?.config?.path ?? row.backend?.path ?? row.path
              ),
            },
          ]
          : []),
      ],
    };
  });
};
