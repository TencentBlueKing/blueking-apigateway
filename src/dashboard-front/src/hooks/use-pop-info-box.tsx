/*
 * Tencent is pleased to support the open source community by making
 * 蓝鲸智云PaaS平台 (BlueKing PaaS) available.
 *
 * Copyright (C) 2021 THL A29 Limited, a Tencent company.  All rights reserved.
 *
 * 蓝鲸智云PaaS平台 (BlueKing PaaS) is licensed under the MIT License.
 *
 * License for 蓝鲸智云PaaS平台 (BlueKing PaaS):
 *
 * ---------------------------------------------------
 * Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
 * documentation files (the "Software"), to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and
 * to permit persons to whom the Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all copies or substantial portions of
 * the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
 * THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
 * CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
 * IN THE SOFTWARE.
 */
/** 基于infoBox二次封装  */
import { type VNode } from 'vue';
import { InfoBox } from 'bkui-vue';
import { isFunction } from 'lodash-es';

type Align = 'center' | 'left' | 'right';
type Theme = 'danger' | 'success' | 'warning' | 'primary';
type InfoType = 'danger' | 'success' | 'warning' | 'loading';

export interface IProps {
  isShow?: boolean;
  width?: number | string;
  class?: string | string[];
  type?: InfoType;
  title?: (() => VNode | string) | VNode | string;
  subTitle?: (() => VNode) | VNode | string;
  content?: (() => VNode) | VNode | string;
  footer?: (() => VNode) | VNode | string;
  headerAlign?: Align;
  footerAlign?: Align;
  contentAlign?: Align;
  showContentBgColor?: boolean;
  showMask?: boolean;
  quickClose?: boolean;
  escClose?: boolean;
  closeIcon?: boolean;
  confirmText?: (() => VNode) | VNode | string;
  cancelText?: (() => VNode) | VNode | string;
  confirmButtonTheme?: Theme;
  beforeClose?: (v: string) => Promise<boolean> | boolean;
  onConfirm?: () => void;
  onCancel?: () => void;
}

export function usePopInfoBox(props: Partial<IProps>) {
  const infoBoxInstance = InfoBox({
    isShow: false,
  });

  const renderTitle = () => {
    if (isFunction(props.title)) {
      return <div class="info-box-title">{props.title?.()}</div>;
    }
    return props.title;
  };

  const renderContent = () => {
    const displayContent = props.subTitle ?? props.content;
    if (isFunction(displayContent)) {
      return <div class="info-box-content">{displayContent?.()}</div>;
    }
    return displayContent;
  };

  const renderInfoBox = () => {
    infoBoxInstance.update({
      ...props,
      title: renderTitle(),
      content: renderContent(),
    });
    infoBoxInstance.show();
  };

  // 是否初始化的时候展示infoBox
  if (props?.isShow) {
    renderInfoBox();
  }
}
