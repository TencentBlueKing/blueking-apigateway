import { debounce } from 'lodash-es';

interface IWidthDivideConfig {
  minWidth?: number // 最小宽度（大于）
  maxWidth?: number // 最大宽度（小于等于）
  divide: string // 对应的分割比例
}

/**
 * 动态计算分割比例的Hook
 * @param customConfig 自定义宽度-比例映射配置
 * @param debounceDelay 防抖延迟时间（默认150ms）
 * @returns 响应式的分割比例值
 */
export const useMcpConfigDivideRatio = (
  customConfig?: WidthDivideConfig[],
  debounceDelay = 150,
) => {
  // 分割比例
  const divideRatio = ref('34%');

  // 预设的宽度-比例配置
  const DEFAULT_CONFIG: WidthDivideConfig[] = [
    {
      maxWidth: 1440,
      divide: '46%',
    },
    {
      minWidth: 1440,
      maxWidth: 1919,
      divide: '40%',
    },
    {
      minWidth: 1920,
      divide: '34%',
    },
  ];

  // 合并配置（优先使用自定义配置）
  const config = customConfig || DEFAULT_CONFIG;

  // 计算不同分辨率下Mcp配置项占比
  const calculateDivide = () => {
    const innerWidth = window.innerWidth;
    // 匹配对应的配置项
    const matchedConfig = config.find((item) => {
      const matchMin = item.minWidth ? innerWidth > item.minWidth : true;
      const matchMax = item.maxWidth ? innerWidth <= item.maxWidth : true;
      return matchMin && matchMax;
    });

    divideRatio.value = matchedConfig?.divide ?? config[config.length - 1].divide;
  };

  const debouncedCalculate = debounce(calculateDivide, debounceDelay);

  onMounted(() => {
    calculateDivide();
    window.addEventListener('resize', debouncedCalculate);
  });

  onUnmounted(() => {
    window.removeEventListener('resize', debouncedCalculate);
  });

  return { divideRatio };
};
