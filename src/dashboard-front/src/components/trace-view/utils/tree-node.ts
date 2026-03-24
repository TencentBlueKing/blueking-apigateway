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

export default class TreeNode {
  // 明确类型：允许任意值，children 是 TreeNode 数组
  value: string | number | unknown;
  children: TreeNode[];

  /**
   * 迭代器包装函数
   */
  static iterFunction<T>(
    fn: (value: unknown, node: TreeNode, depth: number) => T,
    depth = 0,
  ) {
    return (node: TreeNode) => fn(node.value, node, depth);
  }

  /**
   * 搜索匹配函数生成器
   */
  static searchFunction(search: unknown) {
    if (typeof search === 'function') {
      return search as (value: unknown, node: TreeNode) => boolean;
    }

    return (value: string | number | unknown, node: TreeNode): boolean =>
      search instanceof TreeNode ? node === search : value === search;
  }

  constructor(value: string | number | unknown, children: TreeNode[] = []) {
    this.value = value;
    this.children = children;
  }

  /**
   * 获取树的最大深度
   */
  get depth(): number {
    return this.children.reduce(
      (maxDepth, child) => Math.max(child.depth + 1, maxDepth),
      1,
    );
  }

  /**
   * 获取树节点总数
   */
  get size(): number {
    let i = 0;
    this.walk(() => i++);
    return i;
  }

  /**
   * 添加子节点
   */
  addChild(child: unknown | TreeNode): this {
    this.children.push(
      child instanceof TreeNode ? child : new TreeNode(child),
    );
    return this;
  }

  /**
   * 查找节点
   */
  find(search: unknown): TreeNode | null {
    const searchFn = TreeNode.iterFunction(TreeNode.searchFunction(search));
    if (searchFn(this)) {
      return this;
    }

    for (let i = 0; i < this.children.length; i++) {
      const result = this.children[i].find(search);
      if (result) {
        return result;
      }
    }
    return null;
  }

  /**
   * 获取从根节点到目标节点的路径
   */
  getPath(search: unknown): TreeNode[] | null {
    const searchFn = TreeNode.iterFunction(TreeNode.searchFunction(search));

    const findPath = (
      currentNode: TreeNode,
      currentPath: TreeNode[],
    ): TreeNode[] | null => {
      const attempt = currentPath.concat([currentNode]);

      if (searchFn(currentNode)) {
        return attempt;
      }

      for (let i = 0; i < currentNode.children.length; i++) {
        const child = currentNode.children[i];
        const match = findPath(child, attempt);
        if (match) {
          return match;
        }
      }
      return null;
    };

    return findPath(this, []);
  }

  /**
   * 遍历所有叶子节点路径
   */
  paths(fn: (path: unknown[]) => void): unknown[][] {
    const stack: Array<{
      node: TreeNode
      childIndex: number
    }> = [];
    stack.push({
      node: this,
      childIndex: 0,
    });

    const paths: unknown[][] = [];

    while (stack.length) {
      const { node, childIndex } = stack[stack.length - 1];

      if (node.children.length >= childIndex + 1) {
        stack[stack.length - 1].childIndex++;
        stack.push({
          node: node.children[childIndex],
          childIndex: 0,
        });
      }
      else {
        if (node.children.length === 0) {
          const path = stack.map(item => item.node.value);
          paths.push(path);
          fn(path);
        }
        stack.pop();
      }
    }

    return paths;
  }

  /**
   * 深度优先遍历整棵树
   */
  walk(
    fn: (value: unknown, node: TreeNode, depth: number) => void,
    depth = 0,
  ): void {
    const nodeStack: Array<{
      node: TreeNode
      depth: number
    }> = [];
    nodeStack.push({
      node: this,
      depth,
    });

    while (nodeStack.length) {
      const { node, depth: nodeDepth } = nodeStack.pop()!;
      fn(node.value, node, nodeDepth);

      const nextDepth = nodeDepth + 1;
      // 倒序入栈保证遍历顺序
      for (let i = node.children.length - 1; i >= 0; i--) {
        nodeStack.push({
          node: node.children[i],
          depth: nextDepth,
        });
      }
    }
  }
}
