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

import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';

export interface IMarkdownHeading {
  id: string
  name: string
}

export interface IRenderedMarkdown {
  html: string
  headings: IMarkdownHeading[]
}

interface IMarkdownRenderEnv {
  headings: IMarkdownHeading[]
}

interface ICreateMarkdownRendererOptions {
  // 是否给 ### 标题注入 id 并收集标题（API 文档右侧导航需要）
  withHeadingIds?: boolean
}

/**
 * 创建统一的 Markdown 渲染器
 * - 代码块自动包裹复制按钮
 * - 链接默认在新窗口打开
 */
export function createMarkdownRenderer(options?: ICreateMarkdownRendererOptions) {
  const md = new MarkdownIt({
    linkify: false,
    html: true,
    breaks: true,
    highlight(str: string, lang: string) {
      try {
        if (lang && hljs.getLanguage(lang)) {
          return hljs.highlight(str, {
            language: lang,
            ignoreIllegals: true,
          }).value;
        }
      }
      catch {
        return str;
      }
      return str;
    },
  });

  // 代码块：渲染复制按钮，按钮与代码块一起作为 HTML 字符串输出，不会被 Vue 重绘清掉
  const defaultFence = md.renderer.rules.fence || function (tokens, idx, options, env, self) {
    return self.renderToken(tokens, idx, options);
  };
  md.renderer.rules.fence = (tokens, idx, options, env, self) => {
    const html = defaultFence(tokens, idx, options, env, self);
    return `
      <div class="pre-wrapper">
        <button class="ag-copy-btn" type="button">
          <span class="apigateway-icon icon-ag-copy-info"></span>
        </button>
        ${html}
      </div>
    `;
  };

  // 链接：默认新窗口打开
  const defaultLinkOpen = md.renderer.rules.link_open || function (tokens, idx, options, env, self) {
    return self.renderToken(tokens, idx, options);
  };
  md.renderer.rules.link_open = (tokens, idx, options, env, self) => {
    const token = tokens[idx];
    const targetIndex = token.attrIndex('target');
    if (targetIndex < 0) {
      token.attrPush(['target', '_blank']);
    }
    else {
      token.attrs![targetIndex][1] = '_blank';
    }
    const relIndex = token.attrIndex('rel');
    if (relIndex < 0) {
      token.attrPush(['rel', 'noopener noreferrer']);
    }
    else {
      token.attrs![relIndex][1] = 'noopener noreferrer';
    }
    return defaultLinkOpen(tokens, idx, options, env, self);
  };

  const renderMarkdown = (content = ''): IRenderedMarkdown => {
    const renderEnv: IMarkdownRenderEnv = { headings: [] };
    return {
      html: md.render(content, renderEnv),
      headings: renderEnv.headings,
    };
  };

  if (options?.withHeadingIds) {
    md.renderer.rules.heading_open = function (tokens, idx, options, env, self) {
      const curToken = tokens[idx];
      const nextToken = tokens[idx + 1];
      const renderEnv = env as IMarkdownRenderEnv;
      // 找到 ### 标题，并且只包含一行文本的 token
      if (curToken.markup === '###' && nextToken?.type === 'inline') {
        const headingText = nextToken.content;
        const duplicateCount = renderEnv.headings.filter(item => item.name === headingText).length;
        const headingIdText = duplicateCount ? `${headingText}${duplicateCount + 1}` : headingText;
        // 给标题元素ID一个前缀，便于导航目录识别
        const idPrefix = 'doc-heading-';
        curToken.attrPush([
          'id',
          `${idPrefix}${headingIdText}`,
        ]);
        renderEnv.headings.push({
          id: `${idPrefix}${headingIdText}`,
          name: headingText,
        });
      }
      return self.renderToken(tokens, idx, options);
    };
  }

  return {
    md,
    renderMarkdown,
  };
}
