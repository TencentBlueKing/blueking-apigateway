import { t } from '@/locales';
import type {
  AIBackendFallbackItemInput,
  IAIBackendConfigInput,
  IAIBackendInstanceInput,
  IBackendTestConnectionInputSLZ,
} from '@/services/types/body/post/gateways.ts';
import type {
  IAIBackendConfigOutput,
  IAIBackendInstanceOutput,
} from '@/services/types/responses/gateways.ts';

export type AIBackendOptionMode = 'table' | 'text';
export type AIBackendEndpointScheme = 'http' | 'https';
export type AIBackendProvider = IAIBackendInstanceInput['provider'];
export type AIBackendTestStatus = 'untested' | 'testing' | 'success' | 'failed';
export type AIBackendInstanceRole = 'primary' | 'backup';
export type AIBackendBalancerAlgorithm = 'roundrobin' | 'chash';
export type AIBackendFallbackItem = AIBackendFallbackItemInput;
// 影响连通性的实例字段，变更后需要重新测试
export type IAIBackendTestSnapshot = Pick<
  IAIBackendInstanceInput,
  'provider' | 'endpoint' | 'model_endpoint' | 'api_key' | 'auth_header'
>;
export type IStageAIBackendConfigInput = Omit<IAIBackendConfigInput, 'stage_id'>;
// 环境后端接口返回的配置；模型服务详情的配置多一个只读的 stage，也可直接传入
export type IStageAIBackendConfigOutput = Omit<IAIBackendConfigOutput, 'stage'>;

type JsonRecord = Record<string, unknown>;

// 已保存实例的凭据身份。接口返回的凭据是掩码，后端只在 Backend、环境、实例名称都相同时恢复原值；
// 改名、换 Provider、改地址 origin 或认证 Header 名后，原掩码无法沿用，需要重新输入
export interface IAIBackendSavedInstance {
  name: string
  credentialIdentity: string
  apiKey: string
  authHeaderValue: string
}

export interface IAIBackendOptionRow {
  key: string
  value: string
}

export interface IAIBackendInstanceFormData {
  uid: string
  role: AIBackendInstanceRole
  name: string
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
  testStatus: AIBackendTestStatus
  testConfigSnapshot?: IAIBackendTestSnapshot
  initialTestConfigSnapshot?: IAIBackendTestSnapshot
  // 仅从接口回显的实例有值；新增、克隆的实例没有已保存的凭据
  saved?: IAIBackendSavedInstance
}

// 一个环境下的模型服务配置
export interface IAIBackendConfigFormData {
  timeout: number
  instances: IAIBackendInstanceFormData[]
  balancerAlgorithm: AIBackendBalancerAlgorithm
  fallbackStrategy: AIBackendFallbackItem[]
  strategyError: string
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
  expandUntested?: () => void
}

export const AI_BACKEND_SCHEME_OPTIONS: AIBackendEndpointScheme[] = ['http', 'https'];
export const AI_BACKEND_TEST_STATUS_META = {
  untested: {
    theme: 'warning',
    text: t('待测试'),
  },
  testing: {
    theme: 'info',
    text: t('测试中'),
  },
  success: {
    theme: 'success',
    text: t('测试通过'),
  },
  failed: {
    theme: 'danger',
    text: t('测试失败'),
  },
} as const;

export const AI_BACKEND_INSTANCE_PRIORITY: Record<AIBackendInstanceRole, number> = {
  primary: 10,
  backup: 0,
};
export const AI_BACKEND_MAX_BACKUP_COUNT = 1;
export const AI_BACKEND_DEFAULT_FALLBACK_STRATEGY: AIBackendFallbackItem[] = ['http_429', 'http_5xx'];
// 后端禁止作为认证 Header 的名称（不区分大小写）
const AI_BACKEND_FORBIDDEN_AUTH_HEADERS = ['host', 'connection', 'content-length', 'transfer-encoding'];

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
export const getAIBackendOptions = (config: IAIBackendInstanceFormData) => {
  return config.optionMode === 'text'
    ? parseAIBackendOptionsText(config.optionsText)
    : parseAIBackendOptionsTable(config.optionRows);
};

// 地址的 origin（协议、小写主机名、端口，默认端口省略），与后端恢复凭据时的比较方式一致
const getAIBackendUrlOrigin = (url: string) => {
  if (!url) {
    return '';
  }
  try {
    return new URL(url).origin;
  }
  catch {
    // 地址不合法时按原文比较，交给地址校验提示
    return url;
  }
};

// 凭据能否沿用取决于 Provider、Endpoint 和 Models Endpoint 的 origin、认证 Header 名（不区分大小写），
// 地址路径变化不影响。内置 Provider 地址固定，只看 Provider
const getAIBackendCredentialIdentity = (instance: IAIBackendInstanceFormData) => {
  if (isBuiltinAIBackendProvider(instance.provider)) {
    return instance.provider;
  }
  return [
    instance.provider,
    getAIBackendUrlOrigin(`${instance.endpointScheme}://${instance.endpoint.trim()}`),
    getAIBackendUrlOrigin(instance.modelsEndpoint.trim()),
    instance.authHeaderKey.trim().toLowerCase(),
  ].join('|');
};

export const createAIBackendSavedInstance = (instance: IAIBackendInstanceFormData): IAIBackendSavedInstance => ({
  name: instance.name,
  credentialIdentity: getAIBackendCredentialIdentity(instance),
  apiKey: instance.apiKey,
  authHeaderValue: instance.authHeaderValue,
});

// 内置 Provider 的凭据是 API Key，自定义 Provider 的凭据是认证 Header 值
const getAIBackendCredential = (instance: IAIBackendInstanceFormData) => {
  return isBuiltinAIBackendProvider(instance.provider) ? instance.apiKey : instance.authHeaderValue;
};

const getAIBackendSavedCredential = (instance: IAIBackendInstanceFormData) => {
  if (!instance.saved) {
    return '';
  }
  return isBuiltinAIBackendProvider(instance.provider) ? instance.saved.apiKey : instance.saved.authHeaderValue;
};

export const AI_BACKEND_CREDENTIAL_STALE_TEXT = t('实例名称、地址或认证 Header 名已变更，原凭据无法沿用，请重新输入');

// 已保存实例改了名称或连接身份，但凭据还是接口返回的掩码时，后端无法恢复原值，需要重新输入
export const isAIBackendCredentialStale = (instance: IAIBackendInstanceFormData) => {
  const { saved } = instance;
  if (!saved) {
    return false;
  }
  const isIdentityChanged = instance.name !== saved.name
    || getAIBackendCredentialIdentity(instance) !== saved.credentialIdentity;
  if (!isIdentityChanged) {
    return false;
  }
  const credential = getAIBackendCredential(instance);
  return Boolean(credential) && credential === getAIBackendSavedCredential(instance);
};

const AI_BACKEND_CREDENTIAL_MASK_MARK = '****';

// 内置 Provider 的 API Key 不带 Bearer 前缀
const normalizeAIBackendApiKey = (value: string) => value.trim().replace(/^Bearer\s+/i, '');

// 实际提交给后端的凭据
const getAIBackendSubmitCredential = (instance: IAIBackendInstanceFormData) => {
  return isBuiltinAIBackendProvider(instance.provider)
    ? normalizeAIBackendApiKey(instance.apiKey)
    : instance.authHeaderValue.trim();
};

// 与后端一致：只有 ****、「两字符 + **** + 两字符」是保留的掩码形态
const isAIBackendCredentialMaskShape = (value: string) => {
  return value === AI_BACKEND_CREDENTIAL_MASK_MARK
    || (value.length === 8 && value.slice(2, 6) === AI_BACKEND_CREDENTIAL_MASK_MARK);
};

// 输入框里的值是否是接口返回的掩码，用于聚焦时整体选中，方便直接输入新凭据替换
export const isAIBackendSavedCredentialMask = (instance: IAIBackendInstanceFormData, value: string) => {
  return value.includes(AI_BACKEND_CREDENTIAL_MASK_MARK) && value === getAIBackendSavedCredential(instance);
};

// 凭据相关的即时错误：
// - 掩码形态但不是这个实例已保存的掩码（如在掩码上改了一两个字符），后端无法恢复，会拒绝；
// - 已保存实例改了身份但凭据仍是掩码
export const getAIBackendCredentialError = (instance: IAIBackendInstanceFormData) => {
  const credential = getAIBackendSubmitCredential(instance);
  if (isAIBackendCredentialMaskShape(credential) && credential !== getAIBackendSavedCredential(instance)) {
    return t('凭据包含掩码字符 ****，请完整输入新的凭据');
  }
  return isAIBackendCredentialStale(instance) ? AI_BACKEND_CREDENTIAL_STALE_TEXT : '';
};

// 凭据含 **** 但不是保留的掩码形态时，后端会当作新凭据保存。可能是合法凭据，也可能是在掩码上增删了字符，
// 只提示不拦截；如果是后者，连通测试会失败
export const getAIBackendCredentialWarning = (instance: IAIBackendInstanceFormData) => {
  const credential = getAIBackendSubmitCredential(instance);
  if (!credential.includes(AI_BACKEND_CREDENTIAL_MASK_MARK) || isAIBackendCredentialMaskShape(credential)) {
    return '';
  }
  return t('凭据中包含 ****，如果是在已保存的掩码上修改的，请完整输入新的凭据');
};

// 模型服务配置里的所有字段都不支持环境变量引用（如 {env.host}），后端会拒绝。
// 与后端 STAGE_VAR_PATTERN 一致：变量名以字母开头，由字母、数字、下划线组成，最长 50 个字符
const AI_BACKEND_ENV_VAR_REG = /\{env\.[a-zA-Z]\w{0,49}\}/;
export const hasAIBackendEnvVar = (value: string) => AI_BACKEND_ENV_VAR_REG.test(value);
export const AI_BACKEND_ENV_VAR_TEXT = t('模型服务配置不支持环境变量引用');

// 自定义 Provider 没填 Models Endpoint 时，后端只在 Endpoint 路径以 /chat/completions 结尾时推导模型列表地址
export const shouldHintAIBackendModelsEndpoint = (instance: IAIBackendInstanceFormData) => {
  if (isBuiltinAIBackendProvider(instance.provider) || instance.modelsEndpoint.trim() || !instance.endpoint.trim()) {
    return false;
  }
  try {
    const { pathname } = new URL(`${instance.endpointScheme}://${instance.endpoint.trim()}`);
    return !pathname.endsWith('/chat/completions');
  }
  catch {
    // 地址不合法时交给地址校验提示
    return false;
  }
};

export const validateAIBackendInstanceExtra = (config: IAIBackendInstanceFormData) => {
  config.authError = '';
  if (!isBuiltinAIBackendProvider(config.provider)) {
    const headerName = config.authHeaderKey.trim();
    const hasHeaderValue = Boolean(config.authHeaderValue.trim());
    if (Boolean(headerName) !== hasHeaderValue) {
      config.authError = t('认证 Header 名和值需要同时填写');
    }
    else if (AI_BACKEND_FORBIDDEN_AUTH_HEADERS.includes(headerName.toLowerCase())) {
      config.authError = t('认证 Header 不能使用 {name}', { name: headerName });
    }
    else if (hasAIBackendEnvVar(config.authHeaderKey) || hasAIBackendEnvVar(config.authHeaderValue)) {
      config.authError = AI_BACKEND_ENV_VAR_TEXT;
    }
  }
  if (!config.authError) {
    config.authError = getAIBackendCredentialError(config);
  }

  const optionsResult = getAIBackendOptions(config);
  config.optionsError = optionsResult.error;
  if (!config.optionsError && hasAIBackendEnvVar(JSON.stringify(optionsResult.data))) {
    config.optionsError = AI_BACKEND_ENV_VAR_TEXT;
  }
  return !config.authError && !config.optionsError;
};

export const buildAIBackendInstanceSnapshot = (config: IAIBackendInstanceFormData): IAIBackendTestSnapshot => {
  const result: IAIBackendTestSnapshot = {
    provider: config.provider,
  };
  // 内置 Provider 地址固定，不提交 endpoint/model_endpoint，也不使用 auth_header
  if (isBuiltinAIBackendProvider(config.provider)) {
    result.api_key = normalizeAIBackendApiKey(config.apiKey);
    return result;
  }

  // 自定义 Provider 不使用 api_key，认证完整写在 auth_header；可选字段为空时省略，不能传 null
  result.endpoint = `${config.endpointScheme}://${config.endpoint.trim()}`;
  const modelEndpoint = config.modelsEndpoint.trim();
  if (modelEndpoint) {
    result.model_endpoint = modelEndpoint;
  }
  const headerName = config.authHeaderKey.trim();
  const headerValue = config.authHeaderValue.trim();
  if (headerName && headerValue) {
    result.auth_header = {
      name: headerName,
      value: headerValue,
    };
  }
  return result;
};

// 已保存实例的名称原样提交：后端不去除首尾空白，名称变化会导致凭据无法恢复
const getAIBackendInstanceSubmitName = (instance: IAIBackendInstanceFormData) => {
  return instance.saved && instance.name === instance.saved.name ? instance.name : instance.name.trim();
};

export const buildAIBackendInstanceInput = (instance: IAIBackendInstanceFormData): IAIBackendInstanceInput => {
  const result: IAIBackendInstanceInput = {
    name: getAIBackendInstanceSubmitName(instance),
    priority: AI_BACKEND_INSTANCE_PRIORITY[instance.role],
    ...buildAIBackendInstanceSnapshot(instance),
    model_options: getAIBackendOptions(instance).data,
  };
  // 未指定模型时省略字段，不能传空字符串或 null
  const model = instance.model.trim();
  if (model) {
    result.model = model;
  }
  return result;
};

export const buildAIBackendTestParams = (
  instance: IAIBackendInstanceFormData,
  stageId: number,
  backendId?: number,
): IBackendTestConnectionInputSLZ => {
  const params: IBackendTestConnectionInputSLZ = {
    config: {
      instance: buildAIBackendInstanceInput(instance),
    },
  };
  // 新建环境时还没有环境 id（为 0），不传 stage_id
  if (stageId) {
    params.config.stage_id = stageId;
  }
  // backend_id 只用于按 Backend + 环境 + 实例名称恢复已保存实例的脱敏凭据，必须和 stage_id 一起传；
  // 新实例、新环境携带会被后端判为参数错误
  if (backendId && stageId && instance.saved) {
    params.backend_id = backendId;
  }
  return params;
};

export const getAIBackendInstanceCount = (config: IAIBackendConfigFormData, role: AIBackendInstanceRole) => {
  return config.instances.filter(instance => instance.role === role).length;
};

// 至少两个主实例才需要选负载均衡算法
export const shouldShowAIBackendBalancer = (config: IAIBackendConfigFormData) => {
  return getAIBackendInstanceCount(config, 'primary') >= 2;
};

// 实例总数至少两个（含一主一备）才需要故障切换条件
export const shouldShowAIBackendFallback = (config: IAIBackendConfigFormData) => {
  return config.instances.length >= 2;
};

export const AI_BACKEND_PROVIDER_LABEL: Record<AIBackendProvider, string> = {
  'openai': 'OpenAI',
  'deepseek': 'DeepSeek',
  'openai-compatible': 'openai-compatible',
};

// 卡片标题、资源页表格里用来区分实例：有模型显示模型，否则显示自定义 Endpoint 的域名
export const getAIBackendInstanceTarget = (instance: IAIBackendInstanceFormData) => {
  if (instance.model.trim()) {
    return instance.model.trim();
  }
  return instance.provider === 'openai-compatible' ? instance.endpoint.trim().split('/')[0] : '';
};

export const AI_BACKEND_BALANCER_TEXT: Record<AIBackendBalancerAlgorithm, string> = {
  roundrobin: t('轮询'),
  chash: t('按调用方应用一致性哈希'),
};

export const AI_BACKEND_BALANCER_DESC: Record<AIBackendBalancerAlgorithm, string> = {
  roundrobin: t('请求依次分配到各主实例，各实例权重相同'),
  chash: t('同一调用方应用（bk_app_code）的请求固定发往同一主实例，便于复用上游缓存'),
};

export const AI_BACKEND_FALLBACK_TEXT: Record<AIBackendFallbackItem, string> = {
  http_429: t('429 请求超频'),
  http_5xx: t('5xx 服务不可用'),
};

export const getAIBackendInstanceLabel = (config: IAIBackendConfigFormData, index: number) => {
  const instance = config.instances[index];
  if (instance.role === 'backup') {
    return t('备用实例');
  }
  if (getAIBackendInstanceCount(config, 'primary') === 1) {
    return t('主实例');
  }
  const order = config.instances
    .slice(0, index + 1)
    .filter(item => item.role === 'primary')
    .length;
  return `${t('主实例')} ${order}`;
};

export const validateAIBackendStrategy = (config: IAIBackendConfigFormData) => {
  const hasBackup = getAIBackendInstanceCount(config, 'backup') > 0;
  config.strategyError = hasBackup && !config.fallbackStrategy.length
    ? t('添加了备用实例时，至少选择一个故障切换条件')
    : '';
  return !config.strategyError;
};

export const buildAIBackendConfig = (
  config: IAIBackendConfigFormData,
  stageId: number,
): IAIBackendConfigInput => {
  const result: IAIBackendConfigInput = {
    stage_id: stageId,
    timeout: Number(config.timeout),
    instances: config.instances.map(buildAIBackendInstanceInput),
  };
  // 单实例时不提交池级策略
  if (shouldShowAIBackendBalancer(config)) {
    result.balancer = { algorithm: config.balancerAlgorithm };
  }
  // 多实例时总是显式提交：省略会被后端按两项都启用处理，关闭重试只能提交 []
  if (shouldShowAIBackendFallback(config)) {
    result.fallback_strategy = AI_BACKEND_DEFAULT_FALLBACK_STRATEGY
      .filter(item => config.fallbackStrategy.includes(item));
  }
  return result;
};

export const buildStageAIBackendConfig = (config: IAIBackendConfigFormData): IStageAIBackendConfigInput => {
  const { stage_id: _stageId, ...result } = buildAIBackendConfig(config, 0);
  return result;
};

export const getAIBackendFormSnapshot = (config: IAIBackendConfigFormData) => ({
  timeout: config.timeout,
  balancerAlgorithm: config.balancerAlgorithm,
  fallbackStrategy: config.fallbackStrategy,
  instances: config.instances.map(instance => ({
    role: instance.role,
    name: instance.name,
    provider: instance.provider,
    endpointScheme: instance.endpointScheme,
    endpoint: instance.endpoint,
    modelsEndpoint: instance.modelsEndpoint,
    apiKey: instance.apiKey,
    authHeaderKey: instance.authHeaderKey,
    authHeaderValue: instance.authHeaderValue,
    model: instance.model,
    optionMode: instance.optionMode,
    optionRows: instance.optionRows,
    optionsText: instance.optionsText,
  })),
});

// 实例当前应展示的测试状态。已保存实例只改名时连通字段不变，但原掩码凭据已无法恢复，之前的测试结果不再有效
export const getAIBackendInstanceTestStatus = (instance: IAIBackendInstanceFormData): AIBackendTestStatus => {
  if (instance.testStatus === 'success' && isAIBackendCredentialStale(instance)) {
    return 'untested';
  }
  return instance.testStatus;
};

export const isAIBackendInstanceTestPassed = (instance: IAIBackendInstanceFormData) => {
  if (getAIBackendInstanceTestStatus(instance) !== 'success' || !instance.testConfigSnapshot) {
    return false;
  }
  return JSON.stringify(instance.testConfigSnapshot) === JSON.stringify(buildAIBackendInstanceSnapshot(instance));
};

export const isAIBackendConfigTestPassed = (config: IAIBackendConfigFormData) => {
  return config.instances.length > 0 && config.instances.every(isAIBackendInstanceTestPassed);
};

export const getAIBackendConfigTestStatus = (config: IAIBackendConfigFormData): AIBackendTestStatus => {
  const statuses = config.instances.map(getAIBackendInstanceTestStatus);
  if (statuses.includes('testing')) {
    return 'testing';
  }
  if (statuses.includes('failed')) {
    return 'failed';
  }
  return isAIBackendConfigTestPassed(config) ? 'success' : 'untested';
};

export const getAIBackendConfigStatusMeta = (config: IAIBackendConfigFormData) => {
  return AI_BACKEND_TEST_STATUS_META[getAIBackendConfigTestStatus(config)];
};

let instanceUidSeed = 0;
const createInstanceUid = () => {
  instanceUidSeed += 1;
  return `ai-instance-${instanceUidSeed}`;
};

export const createDefaultAIBackendInstanceFormData = (
  role: AIBackendInstanceRole = 'primary',
): IAIBackendInstanceFormData => ({
  uid: createInstanceUid(),
  role,
  name: '',
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
  testStatus: 'untested',
});

export const createDefaultAIBackendConfigFormData = (): IAIBackendConfigFormData => ({
  timeout: 300,
  instances: [createDefaultAIBackendInstanceFormData()],
  balancerAlgorithm: 'roundrobin',
  fallbackStrategy: [...AI_BACKEND_DEFAULT_FALLBACK_STRATEGY],
  strategyError: '',
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

export const getAIBackendConfigStageId = (config: IAIBackendConfigOutput) => Number(config.stage?.id);

const createEditAIBackendInstanceFormData = (
  instance: IAIBackendInstanceOutput,
  role: AIBackendInstanceRole,
): IAIBackendInstanceFormData => {
  const options = instance.model_options || {};
  const optionRows = Object.entries(options).map(([key, value]) => ({
    key,
    value: formatOptionValue(value),
  }));
  const result: IAIBackendInstanceFormData = {
    uid: createInstanceUid(),
    role,
    // 名称是实例身份，原样回显，不能自动去空白或改名
    name: instance.name ?? '',
    provider: instance.provider,
    ...parseEndpoint(instance.endpoint),
    modelsEndpoint: instance.model_endpoint || '',
    apiKey: instance.api_key || '',
    authHeaderKey: instance.auth_header?.name || '',
    authHeaderValue: instance.auth_header?.value || '',
    authError: '',
    model: instance.model || '',
    models: instance.model ? [instance.model] : [],
    optionMode: 'text',
    optionRows: optionRows.length
      ? optionRows
      : [{
        key: '',
        value: '',
      }],
    optionsText: JSON.stringify(options, null, 2),
    optionsError: '',
    testStatus: 'success',
  };
  const snapshot = buildAIBackendInstanceSnapshot(result);
  result.testConfigSnapshot = snapshot;
  result.initialTestConfigSnapshot = snapshot;
  result.saved = createAIBackendSavedInstance(result);
  return result;
};

// 接口统一返回 Web 结构（instances[]，timeout 单位秒），历史数据也已由后端转换
export const createEditAIBackendConfigFormData = (
  config: IStageAIBackendConfigOutput,
): IAIBackendConfigFormData => {
  if (!config.instances?.length) {
    return {
      ...createDefaultAIBackendConfigFormData(),
      timeout: config.timeout || 300,
    };
  }
  const getPriority = (instance: IAIBackendInstanceOutput) => instance.priority ?? AI_BACKEND_INSTANCE_PRIORITY.primary;
  const topPriority = Math.max(...config.instances.map(getPriority));
  const instances = config.instances.map(instance => createEditAIBackendInstanceFormData(
    instance,
    getPriority(instance) < topPriority ? 'backup' : 'primary',
  ));
  const fallbackStrategy = config.fallback_strategy;
  return {
    timeout: config.timeout || 300,
    instances,
    balancerAlgorithm: config.balancer?.algorithm === 'chash' ? 'chash' : 'roundrobin',
    // 历史数据可能没有重试配置：按后端省略时的默认值（两项都启用）回显，由用户确认后保存，不能当作 [] 提交
    fallbackStrategy: Array.isArray(fallbackStrategy)
      ? AI_BACKEND_DEFAULT_FALLBACK_STRATEGY.filter(item => fallbackStrategy.includes(item))
      : [...AI_BACKEND_DEFAULT_FALLBACK_STRATEGY],
    strategyError: '',
  };
};

// 只读展示（如资源页表格）时按接口返回的对象缓存解析结果，避免每次渲染都重新解析
const aiBackendConfigViewCache = new WeakMap<object, IAIBackendConfigFormData>();

export const getAIBackendConfigView = (config: IStageAIBackendConfigOutput) => {
  let view = aiBackendConfigViewCache.get(config);
  if (!view) {
    view = createEditAIBackendConfigFormData(config);
    aiBackendConfigViewCache.set(config, view);
  }
  return view;
};

// 至少两个主实例且选了一致性哈希时，才按调用方应用（bk_app_code）分流，资源必须开启应用认证
export const isAIBackendConfigChash = (config: IStageAIBackendConfigOutput) => {
  const view = getAIBackendConfigView(config);
  return shouldShowAIBackendBalancer(view) && view.balancerAlgorithm === 'chash';
};

// 克隆为新的模型服务时，原服务的凭据无法恢复，需要重新输入并测试
export const resetAIBackendConfigSecrets = (config: IAIBackendConfigFormData) => {
  config.instances.forEach((instance) => {
    instance.apiKey = '';
    instance.authHeaderValue = '';
    instance.testStatus = 'untested';
    instance.testConfigSnapshot = undefined;
    instance.initialTestConfigSnapshot = undefined;
    instance.saved = undefined;
  });
};
