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

import { unescape } from 'lodash-es';
import { type Node, type ScalarTag, isCollection, isMap, isNode, isScalar, isSeq, parseDocument } from 'yaml';

const httpMethods = new Set(['get', 'post', 'put', 'delete', 'patch', 'options', 'head', 'trace']);
const anyMethodKey = 'x-bk-apigateway-method-any';

// 后端 ruamel.yaml 将 1_000 解析为整数，校验路径会使用 [1000]。
const underscoredIntegerKey: ScalarTag = {
  tag: 'tag:yaml.org,2002:int',
  default: 'key',
  test: /^[-+]?\d+_[\d_]*$/,
  resolve: (source) => {
    const value = Number(source.replaceAll('_', ''));
    // 超出安全整数范围时保留原文，避免舍入后匹配到其他键。
    return Number.isSafeInteger(value) ? value : source;
  },
};

const getRoutePrefix = (document: ReturnType<typeof parseDocument>) => {
  const basePath = document.get('basePath');
  if (typeof document.get('swagger') === 'string') {
    return typeof basePath === 'string' ? basePath.replace(/\/+$/, '') : '';
  }

  const serverUrl = document.getIn(['servers', 0, 'url']);
  if (typeof serverUrl !== 'string') {
    return '';
  }
  // 保留 URL 中的原始路径，与后端拼接路由时的语义一致。
  return serverUrl.split(/[?#]/, 1)[0]
    .replace(/^(?:[a-z][\w+.-]*:)?\/\/[^/]*/i, '')
    .replace(/\/+$/, '');
};

// 路径只用于遍历语法树。Schema 错误使用带引号的键和下标，业务错误直接拼接字段名。
function* findNodes(node: Node, path: string, legacy = false, operationMap = false): Generator<Node> {
  if (!path) {
    yield node;
    return;
  }

  if (isSeq(node)) {
    const index = /^\[(0|[1-9]\d*)\]/.exec(path);
    if (index) {
      const item = node.items[Number(index[1])];
      if (isNode(item)) {
        yield* findNodes(item, path.slice(index[0].length), legacy);
      }
    }
    return;
  }

  if (!isMap(node)) {
    return;
  }

  for (const { key, value } of node.items) {
    if (!isScalar(key) || (typeof key.value !== 'string' && typeof key.value !== 'number')) {
      continue;
    }
    const name = String(key.value);
    const quoted = name.replaceAll('\\', '\\\\').replaceAll('\'', '\\\'');
    const segments = typeof key.value === 'number' ? [`[${name}]`] : [`['${quoted}']`, `[${JSON.stringify(name)}]`];
    if (legacy || /^[a-z][a-z\d_]*$/i.test(name)) {
      segments.push(`.${name}`);
    }
    if (operationMap && (httpMethods.has(name) || name === anyMethodKey)) {
      const method = name === anyMethodKey ? 'any' : name;
      segments.push(`.${method.toUpperCase()}`);
      if (name === anyMethodKey) {
        segments.push('.any');
      }
    }

    for (const segment of segments) {
      const rest = path.slice(segment.length);
      if (!path.startsWith(segment) || (rest && !rest.startsWith('.') && !rest.startsWith('['))) {
        continue;
      }
      if (!rest) {
        // 对象或数组可能很长，标记字段名。标量则标记实际的值。
        yield isNode(value) && !isCollection(value) && value.range && value.range[0] < value.range[1] ? value : key;
      }
      else if (isNode(value)) {
        yield* findNodes(value, rest, legacy);
      }
    }
  }
}

function* findLegacyRoute(paths: Node, path: string, prefix: string): Generator<Node> {
  if (!isMap(paths)) {
    return;
  }
  for (const { key, value } of paths.items) {
    if (!isScalar(key) || typeof key.value !== 'string' || !key.value.startsWith('/')) {
      continue;
    }
    const route = `${prefix}/${key.value.replace(/^\/+/, '')}`;
    if (path === route) {
      yield key;
    }
    else if (path.startsWith(`${route}.`) && isNode(value)) {
      yield* findNodes(value, path.slice(route.length), true, true);
    }
  }
}

export const createImportErrorLocator = (source: string) => {
  const document = parseDocument(source, { customTags: [underscoredIntegerKey] });
  const root = document.contents;
  if (document.errors.length || !isMap(root)) {
    return () => undefined;
  }

  const paths = root.get('paths', true);
  const prefix = getRoutePrefix(document);

  return (jsonPath: string): [number, number] | undefined => {
    // 后端对路径做了一次 HTML 转义。只解码用于定位的副本。
    const path = unescape(jsonPath.replaceAll('&#x27;', '&#39;'));
    if (path.length < 2 || !path.startsWith('$')) {
      return;
    }

    const legacyPrefix = `$.paths.${prefix}/`;
    const nodes = path.startsWith(legacyPrefix) && isNode(paths)
      ? findLegacyRoute(paths, path.slice('$.paths.'.length), prefix)
      : findNodes(root, path.slice(1));
    const first = nodes.next();
    if (first.done || !first.value.range || !nodes.next().done) {
      return;
    }
    const [start, end] = first.value.range;
    return start < end ? [start, end] : undefined;
  };
};
