import { t } from '@/locales';
import type { IAIBackendConfigInput } from '@/services/types/body/post/gateways.ts';
import type { IAIBackendConfigOutput } from '@/services/types/responses/gateways.ts';

export type AIBackendOptionMode = 'table' | 'text';
export type AIBackendEndpointScheme = 'http' | 'https';
export type AIBackendProvider = IAIBackendConfigInput['provider'];
export type AIBackendTestStatus = 'untested' | 'testing' | 'success' | 'failed';
export type IAIBackendTestSnapshot = IAIBackendConfigInput;
export type IStageAIBackendConfigInput = Omit<IAIBackendConfigInput, 'stage_id'>;
export type IStageAIBackendConfigOutput = Omit<IAIBackendConfigOutput, 'stage_id'>;

type JsonRecord = Record<string, unknown>;

export interface IInternalAIBackendConfigOutput {
  timeout: number
  instances: {
    name: string
    provider: AIBackendProvider
    weight: number
    auth?: {
      header?: Record<string, string>
    }
    options: Record<string, unknown>
    override?: {
      endpoint: string
    }
  }[]
  stage?: {
    id: number
    name: string
  }
}

export type ICompatibleAIBackendConfigOutput = IStageAIBackendConfigOutput | IInternalAIBackendConfigOutput;

export interface IAIBackendOptionRow {
  key: string
  value: string
}

export interface IAIBackendConfigFormData {
  provider: AIBackendProvider
  endpointScheme: AIBackendEndpointScheme
  endpoint: string
  modelsEndpoint: string
  apiKey: string
  authHeaderKey: string
  authHeaderValue: string
  authError: string
  model: string
  models: string[]
  optionMode: AIBackendOptionMode
  optionRows: IAIBackendOptionRow[]
  optionsText: string
  optionsError: string
  timeout: number
  testStatus: AIBackendTestStatus
  testConfigSnapshot?: IAIBackendTestSnapshot
  initialTestConfigSnapshot?: IAIBackendTestSnapshot
}

interface IOptionsResult {
  data: JsonRecord
  error: string
}

interface IJsonErrorLocation {
  line: number
  column: number
}

export interface IAIBackendConfigFormMethod {
  validate: () => Promise<boolean>
}

export const AI_BACKEND_PROVIDER_OPTIONS: AIBackendProvider[] = ['openai', 'deepseek', 'openai-compatible'];
export const AI_BACKEND_SCHEME_OPTIONS: AIBackendEndpointScheme[] = ['http', 'https'];
export const AI_BACKEND_TEST_STATUS_META = {
  untested: {
    theme: 'warning',
    tagTheme: 'warning',
    text: t('未测试'),
  },
  testing: {
    theme: 'info',
    tagTheme: 'loading',
    text: t('测试中'),
  },
  success: {
    theme: 'success',
    tagTheme: 'running',
    text: t('已测试'),
  },
  failed: {
    theme: 'danger',
    tagTheme: 'danger',
    text: t('测试失败'),
  },
} as const;

const defaultOptionsText = JSON.stringify({ temperature: 0.7 }, null, 2);

export const isBuiltinAIBackendProvider = (provider: AIBackendProvider) => provider !== 'openai-compatible';

export const isValidAIBackendHttpUrl = (value: string) => {
  try {
    const url = new URL(value);
    return ['http:', 'https:'].includes(url.protocol)
      && Boolean(url.hostname)
      && !url.username
      && !url.password;
  }
  catch {
    return false;
  }
};

const getJsonSyntaxErrorPosition = (value: string): number | null => {
  let index = 0;
  let errorPosition = value.length;
  let parseValue = () => false;

  const fail = (position = index) => {
    errorPosition = Math.min(position, value.length);
    return false;
  };
  const skipWhitespace = () => {
    while (' \n\r\t'.includes(value[index])) {
      index += 1;
    }
  };
  const parseString = () => {
    if (value[index] !== '"') {
      return fail();
    }
    index += 1;
    while (index < value.length) {
      const char = value[index];
      if (char === '"') {
        index += 1;
        return true;
      }
      if (char === '\\') {
        index += 1;
        const escapedChar = value[index];
        if ('"\\/bfnrt'.includes(escapedChar)) {
          index += 1;
          continue;
        }
        if (escapedChar === 'u') {
          for (let offset = 1; offset <= 4; offset++) {
            if (!/[\da-f]/i.test(value[index + offset] || '')) {
              return fail(index + offset);
            }
          }
          index += 5;
          continue;
        }
        return fail();
      }
      if (char.charCodeAt(0) <= 0x1f) {
        return fail();
      }
      index += 1;
    }
    return fail(value.length);
  };
  const parseNumber = () => {
    const matched = value.slice(index).match(/^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?/);
    if (!matched) {
      return fail();
    }
    index += matched[0].length;
    return true;
  };
  const parseLiteral = (literal: 'true' | 'false' | 'null') => {
    for (let offset = 0; offset < literal.length; offset++) {
      if (value[index + offset] !== literal[offset]) {
        return fail(index + offset);
      }
    }
    index += literal.length;
    return true;
  };
  const parseObject = () => {
    index += 1;
    skipWhitespace();
    if (value[index] === '}') {
      index += 1;
      return true;
    }
    while (index < value.length) {
      if (!parseString()) {
        return false;
      }
      skipWhitespace();
      if (value[index] !== ':') {
        return fail();
      }
      index += 1;
      if (!parseValue()) {
        return false;
      }
      skipWhitespace();
      if (value[index] === '}') {
        index += 1;
        return true;
      }
      if (value[index] !== ',') {
        return fail();
      }
      index += 1;
      skipWhitespace();
    }
    return fail(value.length);
  };
  const parseArray = () => {
    index += 1;
    skipWhitespace();
    if (value[index] === ']') {
      index += 1;
      return true;
    }
    while (index < value.length) {
      if (!parseValue()) {
        return false;
      }
      skipWhitespace();
      if (value[index] === ']') {
        index += 1;
        return true;
      }
      if (value[index] !== ',') {
        return fail();
      }
      index += 1;
      skipWhitespace();
    }
    return fail(value.length);
  };

  parseValue = () => {
    skipWhitespace();
    const char = value[index];
    if (char === '{') {
      return parseObject();
    }
    if (char === '[') {
      return parseArray();
    }
    if (char === '"') {
      return parseString();
    }
    if (char === 't' || char === 'f' || char === 'n') {
      return parseLiteral(char === 't' ? 'true' : char === 'f' ? 'false' : 'null');
    }
    if (char === '-' || /\d/.test(char)) {
      return parseNumber();
    }
    return fail();
  };

  if (!parseValue()) {
    return errorPosition;
  }
  skipWhitespace();
  return index === value.length ? null : index;
};

const getJsonErrorLocation = (value: string, message: string): IJsonErrorLocation | null => {
  const lineColumnMatch = message.match(/line\s+(\d+)\s+column\s+(\d+)/i);
  if (lineColumnMatch) {
    return {
      line: Number(lineColumnMatch[1]),
      column: Number(lineColumnMatch[2]),
    };
  }

  const positionMatch = message.match(/position\s+(\d+)/i);
  const position = positionMatch ? Number(positionMatch[1]) : getJsonSyntaxErrorPosition(value);
  if (position === null) {
    return null;
  }

  const lines = value.slice(0, Math.min(position, value.length)).split(/\r\n|\r|\n/);
  return {
    line: lines.length,
    column: lines[lines.length - 1].length + 1,
  };
};

const getJsonErrorReason = (message: string) => {
  const positionSuffixReg = /\s+at position\s+\d+(?:\s+\(line\s+\d+\s+column\s+\d+\))?\.?$/i;
  const lineColumnSuffixReg = /\s+at line\s+\d+\s+column\s+\d+(?:\s+of the JSON data)?\.?$/i;
  return message
    .replace(positionSuffixReg, '')
    .replace(lineColumnSuffixReg, '');
};

const formatJsonParseError = (value: string, error: unknown) => {
  const message = error instanceof Error ? error.message : '';
  if (!message) {
    return t('请输入合法 JSON 对象');
  }

  const location = getJsonErrorLocation(value, message);
  const reason = getJsonErrorReason(message);
  if (!location) {
    return t('JSON 格式错误：{message}', { message: reason });
  }
  return t('第 {line} 行，第 {column} 列：{message}', {
    line: location.line,
    column: location.column,
    message: reason,
  });
};

export const parseAIBackendOptionsText = (value: string): IOptionsResult => {
  try {
    const data = JSON.parse(value || '{}');
    if (!data || Array.isArray(data) || typeof data !== 'object') {
      return {
        data: {},
        error: t('请输入合法 JSON 对象'),
      };
    }
    if (Object.hasOwn(data, 'model')) {
      return {
        data: {},
        error: t('Model Options 不能包含 model 字段'),
      };
    }
    return {
      data,
      error: '',
    };
  }
  catch (error) {
    return {
      data: {},
      error: formatJsonParseError(value, error),
    };
  }
};

const parseOptionValue = (value: string) => {
  const normalizedValue = value.trim();
  if (!normalizedValue) {
    return '';
  }
  try {
    return JSON.parse(normalizedValue);
  }
  catch {
    return value;
  }
};

export const parseAIBackendOptionsTable = (rows: IAIBackendOptionRow[]): IOptionsResult => {
  const data: JsonRecord = {};
  for (const row of rows) {
    const key = row.key.trim();
    if (!key && !row.value.trim()) {
      continue;
    }
    if (!key || Object.hasOwn(data, key)) {
      return {
        data: {},
        error: t('参数名不能为空且不能重复'),
      };
    }
    if (key === 'model') {
      return {
        data: {},
        error: t('Model Options 不能包含 model 字段'),
      };
    }
    data[key] = parseOptionValue(row.value);
  }
  return {
    data,
    error: '',
  };
};

export const getAIBackendOptions = (config: IAIBackendConfigFormData) => {
  return config.optionMode === 'text'
    ? parseAIBackendOptionsText(config.optionsText)
    : parseAIBackendOptionsTable(config.optionRows);
};

export const validateAIBackendConfigExtra = (config: IAIBackendConfigFormData) => {
  if (isBuiltinAIBackendProvider(config.provider)) {
    config.authError = '';
  }
  else {
    const hasHeaderKey = Boolean(config.authHeaderKey.trim());
    const hasHeaderValue = Boolean(config.authHeaderValue.trim());
    config.authError = hasHeaderKey === hasHeaderValue ? '' : t('认证 Header 名和值需要同时填写');
  }

  const optionsResult = getAIBackendOptions(config);
  config.optionsError = optionsResult.error;
  return !config.authError && !config.optionsError;
};

export const buildAIBackendConfig = (
  config: IAIBackendConfigFormData,
  stageId: number,
): IAIBackendConfigInput => {
  const result: IAIBackendConfigInput = {
    stage_id: stageId,
    provider: config.provider,
    model: config.model.trim() || null,
    model_options: getAIBackendOptions(config).data,
    timeout: Number(config.timeout),
  };
  if (isBuiltinAIBackendProvider(config.provider)) {
    result.api_key = config.apiKey.trim();
    return result;
  }

  result.endpoint = `${config.endpointScheme}://${config.endpoint.trim()}`;
  result.model_endpoint = config.modelsEndpoint.trim() || null;
  result.api_key = null;
  result.auth_header = config.authHeaderKey.trim() && config.authHeaderValue.trim()
    ? {
      name: config.authHeaderKey.trim(),
      value: config.authHeaderValue.trim(),
    }
    : null;
  return result;
};

export const buildStageAIBackendConfig = (config: IAIBackendConfigFormData): IStageAIBackendConfigInput => {
  const { stage_id: _stageId, ...result } = buildAIBackendConfig(config, 0);
  return result;
};

export const getAIBackendFormSnapshot = (config: IAIBackendConfigFormData) => ({
  provider: config.provider,
  endpointScheme: config.endpointScheme,
  endpoint: config.endpoint,
  modelsEndpoint: config.modelsEndpoint,
  apiKey: config.apiKey,
  authHeaderKey: config.authHeaderKey,
  authHeaderValue: config.authHeaderValue,
  model: config.model,
  optionMode: config.optionMode,
  optionRows: config.optionRows,
  optionsText: config.optionsText,
  timeout: config.timeout,
});

export const isAIBackendConfigTestPassed = (config: IAIBackendConfigFormData, stageId: number) => {
  if (config.testStatus !== 'success' || !config.testConfigSnapshot) {
    return false;
  }
  return JSON.stringify(config.testConfigSnapshot) === JSON.stringify(buildAIBackendConfig(config, stageId));
};

export const createDefaultAIBackendConfigFormData = (): IAIBackendConfigFormData => ({
  provider: 'openai-compatible',
  endpointScheme: 'https',
  endpoint: '',
  modelsEndpoint: '',
  apiKey: '',
  authHeaderKey: '',
  authHeaderValue: '',
  authError: '',
  model: '',
  models: [],
  optionMode: 'text',
  optionRows: [{
    key: 'temperature',
    value: '0.7',
  }],
  optionsText: defaultOptionsText,
  optionsError: '',
  timeout: 300,
  testStatus: 'untested',
});

const parseEndpoint = (endpoint = '') => {
  const matched = endpoint.match(/^(https?):\/\/(.*)$/i);
  return {
    endpointScheme: (matched?.[1]?.toLowerCase() || 'https') as AIBackendEndpointScheme,
    endpoint: matched?.[2] || endpoint,
  };
};

const formatOptionValue = (value: unknown) => {
  return typeof value === 'string' ? value : JSON.stringify(value) ?? '';
};

const normalizeInternalAIBackendConfig = (
  config: IInternalAIBackendConfigOutput,
): IStageAIBackendConfigOutput => {
  const instance = config.instances[0];
  const {
    model,
    ...modelOptions
  } = instance?.options || {};
  const headers = Object.entries(instance?.auth?.header || {});
  const authorizationHeader = headers.find(([name]) => name.toLowerCase() === 'authorization');
  const [authHeaderKey = '', authHeaderValue = ''] = headers[0] || [];
  const apiKey = authorizationHeader?.[1] || '';
  return {
    provider: instance?.provider || 'openai-compatible',
    endpoint: instance?.override?.endpoint || '',
    model_endpoint: null,
    api_key: apiKey.startsWith('Bearer ') ? apiKey.slice(7) : apiKey,
    auth_header: authHeaderKey && authHeaderValue
      ? {
        name: authHeaderKey,
        value: authHeaderValue,
      }
      : null,
    model: typeof model === 'string' ? model : null,
    model_options: modelOptions,
    timeout: Math.max(1, Math.round(Number(config.timeout) / 1000)),
  };
};

const normalizeAIBackendConfig = (
  config: ICompatibleAIBackendConfigOutput,
): IStageAIBackendConfigOutput => {
  return 'instances' in config
    ? normalizeInternalAIBackendConfig(config)
    : config;
};

export const getAIBackendConfigStageId = (
  config: IAIBackendConfigOutput | IInternalAIBackendConfigOutput,
) => {
  return 'stage_id' in config ? Number(config.stage_id) : Number(config.stage?.id);
};

export const createEditAIBackendConfigFormData = (
  config: ICompatibleAIBackendConfigOutput,
  stageId: number,
): IAIBackendConfigFormData => {
  const normalizedConfig = normalizeAIBackendConfig(config);
  const options = normalizedConfig.model_options || {};
  const endpoint = parseEndpoint(normalizedConfig.endpoint);
  const optionRows = Object.entries(options).map(([key, value]) => ({
    key,
    value: formatOptionValue(value),
  }));
  const result: IAIBackendConfigFormData = {
    provider: normalizedConfig.provider,
    ...endpoint,
    modelsEndpoint: normalizedConfig.model_endpoint || '',
    apiKey: normalizedConfig.api_key || '',
    authHeaderKey: normalizedConfig.auth_header?.name || '',
    authHeaderValue: normalizedConfig.auth_header?.value || '',
    authError: '',
    model: normalizedConfig.model || '',
    models: normalizedConfig.model ? [normalizedConfig.model] : [],
    optionMode: 'text',
    optionRows: optionRows.length
      ? optionRows
      : [{
        key: '',
        value: '',
      }],
    optionsText: JSON.stringify(options, null, 2),
    optionsError: '',
    timeout: normalizedConfig.timeout,
    testStatus: 'success',
  };
  const snapshot = buildAIBackendConfig(result, stageId);
  result.testConfigSnapshot = snapshot;
  result.initialTestConfigSnapshot = snapshot;
  return result;
};
