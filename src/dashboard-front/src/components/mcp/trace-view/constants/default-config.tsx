/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2026 Tencent. All rights reserved.
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

import { FALLBACK_DAG_MAX_NUM_SERVICES } from './index';

// 手动实现深度冻结函数
export function deepFreeze<T>(obj: T): Readonly<T> {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }

  Object.freeze(obj);

  const propertyNames = Object.getOwnPropertyNames(obj);
  for (const name of propertyNames) {
    const value = (obj as any)[name];

    if (typeof value === 'object' && value !== null && !Object.isFrozen(value)) {
      deepFreeze(value);
    }
  }

  return obj as Readonly<T>;
}

export default deepFreeze(
  Object.defineProperty(
    {
      archiveEnabled: false,
      dependencies: {
        dagMaxNumServices: FALLBACK_DAG_MAX_NUM_SERVICES,
        menuEnabled: true,
      },
      linkPatterns: [],
      qualityMetrics: {
        menuEnabled: false,
        menuLabel: 'Trace Quality',
      },
      menu: [
        {
          label: 'About Jaeger',
          items: [
            {
              label: 'Website/Docs',
              url: 'https://www.jaegertracing.io/',
            },
            {
              label: 'Blog',
              url: 'https://medium.com/jaegertracing/',
            },
            {
              label: 'Twitter',
              url: 'https://twitter.com/JaegerTracing',
            },
            {
              label: 'Discussion Group',
              url: 'https://groups.google.com/forum/#!forum/jaeger-tracing',
            },
            {
              label: 'Online Chat',
              url: 'https://cloud-native.slack.com/archives/CGG7NFUJ3',
            },
            {
              label: 'GitHub',
              url: 'https://github.com/jaegertracing/',
            },
            {},
            {},
            {},
            {},
          ],
        },
      ],
      search: {
        maxLookback: {
          label: '2 Days',
          value: '2d',
        },
        maxLimit: 1500,
      },
      tracking: {
        gaID: null,
        trackErrors: true,
        customWebAnalytics: null,
      },
      monitor: {
        menuEnabled: true,
        emptyState: {
          mainTitle: 'Get started with Service Performance Monitoring',
          subTitle:
            'A high-level monitoring dashboard that helps you cut down the time to identify and resolve anomalies and issues.',
          description:
            'Service Performance Monitoring aggregates tracing data into RED metrics and visualizes them in service and operation level dashboards.',
          button: {
            text: 'Read the Documentation',
            onClick: () => window.open('https://www.jaegertracing.io/docs/latest/spm/'),
          },
          alert: {
            message: 'Service Performance Monitoring requires a Prometheus-compatible time series database.',
            type: 'info',
          },
        },
        docsLink: 'https://www.jaegertracing.io/docs/latest/spm/',
      },
    },
    // fields that should be individually merged vs wholesale replaced
    '__mergeFields',
    { value: ['dependencies', 'search', 'tracking'] },
  ),
);

export const deprecations = [
  {
    formerKey: 'dependenciesMenuEnabled',
    currentKey: 'dependencies.menuEnabled',
  },
  {
    formerKey: 'gaTrackingID',
    currentKey: 'tracking.gaID',
  },
];
