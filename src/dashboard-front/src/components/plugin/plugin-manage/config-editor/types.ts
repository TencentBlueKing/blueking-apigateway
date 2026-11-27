import type { Component } from 'vue';

interface ICustomEditor {
  kind: 'custom'
  component: Component
}

interface IWhitelistEditor {
  kind: 'whitelist'
  component: Component
}

interface IEmptyEditor {
  kind: 'none'
}

export type PluginEditorDefinition = ICustomEditor | IWhitelistEditor | IEmptyEditor;

export interface IPluginDefinition {
  editor: PluginEditorDefinition
  notice?: string
}

export interface IPluginFormHandle {
  getValue: () => unknown | Promise<unknown>
  clearValidate?: () => void
}

export interface IWhitelistFormHandle {
  sendPolicyData: () => {
    data: string
    error: boolean
  }
}

export type PluginFormHandle = IPluginFormHandle | IWhitelistFormHandle;
