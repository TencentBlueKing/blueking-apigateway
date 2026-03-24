/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
 * Copyright (C) 2026 Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License.
 * http://opensource.org/licenses/MIT
 */

import _get from 'lodash-es/get';
import type { ISpan } from '@/components/trace-view/typings';
import spanAncestorIds from '@/components/trace-view/utils/span-ancestor-ids';
import AgIcon from '@/components/ag-icon/Index.vue';

import './span-tree-offset.scss';

export default defineComponent({
  name: 'SpanTreeOffset',

  props: {
    childrenVisible: {
      type: Boolean,
      default: false,
    },

    onClick: {
      type: Function as PropType<(event: MouseEvent) => void>,

      default: (): (() => void) => () => {
      },
    },

    span: {
      type: Object as PropType<ISpan | undefined>,
      required: true,
    },

    showChildrenIcon: {
      type: Boolean,
      default: false,
    },
  },

  emits: [
    'addHoverIndentGuideId',
    'removeHoverIndentGuideId',
  ],

  setup(props, { emit }) {
    // 处理缩进层级 ID
    const processedAncestorIds = computed(() => {
      const ids = spanAncestorIds(props.span);
      ids.push('root');
      return ids.reverse();
    });

    const indentWidth = computed(() => {
      // 获取当前 span 的深度 depth，没有则默认为 0
      const depth = props.span?.depth ?? 0;

      // 如果 depth 为 0（最顶层节点），缩进宽度 = 0px
      if (!depth) {
        return '3px';
      }

      // 如果当前节点【有子节点】
      if (props?.span?.hasChildren) {
        return `${4 + depth * 28}px`;
      }

      // 如果当前节点【没有子节点】
      return `${12 + 16 + depth * 28}px`;
    });

    // 图标名称
    const iconName = computed(() => {
      const { hasChildren } = props.span ?? {};
      if (hasChildren || props.showChildrenIcon) {
        return 'down-small';
      }
      return undefined;
    });

    // 鼠标事件
    const handleMouseEnter = (event: MouseEvent, ancestorId: string) => {
      if (
        !(event.relatedTarget instanceof HTMLSpanElement)
        || _get(event, 'relatedTarget.dataset.ancestorId') !== ancestorId
      ) {
        emit('addHoverIndentGuideId', ancestorId);
      }
    };

    const handleMouseLeave = (event: MouseEvent, ancestorId: string) => {
      if (
        !(event.relatedTarget instanceof HTMLSpanElement)
        || _get(event, 'relatedTarget.dataset.ancestorId') !== ancestorId
      ) {
        emit('removeHoverIndentGuideId', ancestorId);
      }
    };

    return {
      iconName,
      processedAncestorIds,
      indentWidth,
      handleMouseEnter,
      handleMouseLeave,
    };
  },

  render() {
    const {
      span,
      childrenVisible,
      iconName,
      processedAncestorIds,
      indentWidth,
      onClick,
      handleMouseEnter,
      handleMouseLeave,
    } = this;

    const { hasChildren, span_id = '' } = span ?? {};

    const wrapperProps = hasChildren
      ? {
        'onClick': (e: MouseEvent) => onClick?.(e),
        'role': 'switch',
        'aria-checked': childrenVisible,
        'class': 'span-tree-offset is-parent',
        // 动态绑定左间距
        'style': { paddingLeft: indentWidth },
      }
      : {
        class: 'span-tree-offset',
        // 无子节点也强制偏移，永远层级缩进
        style: { paddingLeft: indentWidth },
      };

    // 图标容器类名
    const iconWrapperClass = [
      'span-tree-offset-icon-wrapper',
      'color-[#979ba5]',
      !childrenVisible && 'rotate-[-90deg]',
    ].filter(Boolean);

    return h(
      'span',
      wrapperProps,
      [
        // 缩进引导线（保留原有逻辑）
        ...processedAncestorIds.map(id =>
          h('span', {
            'key': id,
            'class': 'span-tree-offset-indent-guide',
            'data-ancestor-id': id,
            'onMouseenter': (e: MouseEvent) => handleMouseEnter(e, id),
            'onMouseleave': (e: MouseEvent) => handleMouseLeave(e, id),
          }),
        ),

        iconName && h(
          'span',
          {
            class: iconWrapperClass,
            onMouseenter: (e: MouseEvent) => handleMouseEnter(e, span_id),
            onMouseleave: (e: MouseEvent) => handleMouseLeave(e, span_id),
          },
          h(AgIcon, {
            name: iconName,
            size: '24',
            class: 'vertical-middle',
          }),
        ),
      ],
    );
  },
});
