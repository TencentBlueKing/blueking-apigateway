import type { Component } from 'vue';

export interface IPluginFormConfig {
  schema: Record<string, any>
  layout?: Record<string, any> | unknown[]
}

interface ICustomEditor {
  kind: 'custom'
  component: Component
}

interface ISchemaEditor {
  kind: 'schema'
  component: Component
  getFormConfig: (locale: string) => IPluginFormConfig
}

interface IWhitelistEditor {
  kind: 'whitelist'
  component: Component
}

interface IEmptyEditor {
  kind: 'none'
}

export type PluginEditorDefinition = ICustomEditor | ISchemaEditor | IWhitelistEditor | IEmptyEditor;

export interface IPluginDefinition {
  editor: PluginEditorDefinition
  notice?: string
}

export interface IPluginFormHandle {
  getValue: () => unknown | Promise<unknown>
  clearValidate?: () => void
}

export interface ISchemaPluginFormHandle extends IPluginFormHandle {
  validate: () => Promise<boolean | undefined>
}

export interface IWhitelistFormHandle {
  sendPolicyData: () => {
    data: string
    error: boolean
  }
}

export type PluginFormHandle = IPluginFormHandle | ISchemaPluginFormHandle | IWhitelistFormHandle;
