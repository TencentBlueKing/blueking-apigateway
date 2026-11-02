import { isPlainObject } from 'lodash-es';
import { PluginEditorError } from '@/components/plugin-manage/config-editor/form-adapter';

export interface IUserRateLimitRule {
  period: number
  tokens: number
}

export interface IUserRateLimitConfig {
  rates: Record<string, IUserRateLimitRule[]>
}

export interface IUserRateLimitRow extends IUserRateLimitRule {
  id: number
  username: string
}

export interface IUserRateLimitFormData {
  default: IUserRateLimitRule
  specials: IUserRateLimitRow[]
}

let nextRowId = 0;

export const createUserRateLimitRow = (
  username = '',
  tokens = 100,
  period = 1,
): IUserRateLimitRow => ({
  id: nextRowId++,
  username,
  tokens,
  period,
});

export const isPositiveInteger = (value: unknown): boolean =>
  typeof value === 'number' && Number.isSafeInteger(value) && value > 0;

export const getUserRateLimitFormData = (config: Record<string, unknown>): IUserRateLimitFormData => {
  if (!Object.hasOwn(config, 'rates')) {
    return {
      default: {
        period: 1,
        tokens: 100,
      },
      specials: [],
    };
  }
  if (!isPlainObject(config.rates)) {
    throw new PluginEditorError('插件配置格式错误，请检查后重试');
  }

  const rates = config.rates as Record<string, unknown>;
  // 默认限制固定为一条，异常数据直接报错，避免回显时静默丢弃额外规则。
  if (!Array.isArray(rates.__default) || rates.__default.length !== 1) {
    throw new PluginEditorError('插件配置格式错误，请检查后重试');
  }

  const form: IUserRateLimitFormData = {
    default: {
      period: 1,
      tokens: 100,
    },
    specials: [],
  };
  for (const [username, rules] of Object.entries(rates)) {
    if (!username.trim() || !Array.isArray(rules) || !rules.length) {
      throw new PluginEditorError('插件配置格式错误，请检查后重试');
    }
    for (const rule of rules) {
      if (!isPlainObject(rule) || !isPositiveInteger(rule.tokens) || !isPositiveInteger(rule.period)) {
        throw new PluginEditorError('插件配置格式错误，请检查后重试');
      }
      if (username === '__default') {
        form.default = {
          period: rule.period,
          tokens: rule.tokens,
        };
      }
      else {
        form.specials.push(createUserRateLimitRow(username, rule.tokens, rule.period));
      }
    }
  }
  return form;
};

// 同一用户只能出现一次，用户名不同则允许配置相同的次数和周期。
export const hasDuplicateUsername = (rows: IUserRateLimitRow[], current: IUserRateLimitRow): boolean =>
  !!current.username.trim()
  && rows.some(row => row.id !== current.id && row.username === current.username);

export const getUserRateLimitConfig = (form: IUserRateLimitFormData): IUserRateLimitConfig => {
  if (!form.default || !isPositiveInteger(form.default.tokens) || !isPositiveInteger(form.default.period)) {
    throw new PluginEditorError('请输入正整数');
  }

  // 每个用户只输出一条规则，保留后端要求的数组结构。
  const rates = new Map<string, IUserRateLimitRule[]>([['__default', [{ ...form.default }]]]);
  for (const row of form.specials) {
    if (!row.username.trim()) {
      throw new PluginEditorError('请选择用户');
    }
    if (row.username === '__default') {
      throw new PluginEditorError('用户名不能为 __default');
    }
    if (!isPositiveInteger(row.tokens) || !isPositiveInteger(row.period)) {
      throw new PluginEditorError('请输入正整数');
    }
    if (hasDuplicateUsername(form.specials, row)) {
      throw new PluginEditorError('同一用户只能配置一条频率限制');
    }
    rates.set(row.username, [{
      period: row.period,
      tokens: row.tokens,
    }]);
  }
  return { rates: Object.fromEntries(rates) };
};
