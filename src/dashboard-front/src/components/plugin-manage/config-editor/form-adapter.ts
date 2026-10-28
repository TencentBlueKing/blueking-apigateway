import { isPlainObject } from 'lodash-es';
import { json2Yaml } from '@/utils/json2Yaml';
import { yaml2Json } from '@/utils/yaml2Json';
import type { ISchemaPluginFormHandle, PluginEditorDefinition, PluginFormHandle } from './types';

export class PluginEditorError extends Error {
}

// 现有表单自行展示校验提示，将校验失败与配置解析、序列化错误区分开，
// 后两类错误需要由外层统一展示提示。
export class PluginValidationError extends Error {
}

export const parsePluginConfig = (yaml?: string | null): Record<string, any> => {
  if (!yaml?.trim()) {
    return {};
  }
  const result = yaml2Json(yaml);
  if (result.error || !isPlainObject(result.data)) {
    throw new PluginEditorError('插件配置格式错误，请检查后重试');
  }
  return result.data as Record<string, any>;
};

export const serializePluginConfig = (config: unknown): string => {
  if (!isPlainObject(config)) {
    throw new PluginEditorError('插件配置转换失败');
  }
  try {
    const result = json2Yaml(JSON.stringify(config));
    if (!result.error) {
      return result.data;
    }
  }
  catch {
    // 调用 YAML 转换函数前，JSON.stringify 本身也可能失败。
  }
  throw new PluginEditorError('插件配置转换失败');
};

export const collectPluginYaml = async (
  editor: PluginEditorDefinition,
  form: PluginFormHandle | null,
): Promise<string> => {
  if (editor.kind === 'none') {
    return '{}';
  }
  if (!form) {
    throw new PluginEditorError('表单加载失败');
  }
  if (editor.kind === 'whitelist') {
    if (!('sendPolicyData' in form)) {
      throw new PluginEditorError('表单加载失败');
    }
    const result = form.sendPolicyData();
    if (result.error || !result.data) {
      throw new PluginEditorError('插件配置转换失败');
    }
    return result.data;
  }
  if (!('getValue' in form) || (editor.kind === 'schema' && !('validate' in form))) {
    throw new PluginEditorError('表单加载失败');
  }

  let config: unknown;
  try {
    // 自定义表单已在 getValue() 内完成校验；Schema 表单单独返回布尔校验结果，
    // 必须先通过校验，再读取配置值。
    if (editor.kind === 'schema' && !await (form as ISchemaPluginFormHandle).validate()) {
      throw new PluginValidationError();
    }
    config = await form.getValue();
  }
  catch (error) {
    if (error instanceof PluginValidationError) {
      throw error;
    }
    throw new PluginValidationError();
  }
  return serializePluginConfig(config);
};
