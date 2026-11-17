// 企业微信建群请求
export interface ICreateChatInput {
  bk_app_code: string
  name: string
  owner: string
  userlist: string[]
}

// 企业微信发送文本消息请求
export interface ISendChatInput {
  bk_app_code: string
  chatid: string
  msgtype: string
  text: { content: string }
}

// 企业微信建群接口，按当前前端消费的字段声明
export interface ICreateChatOutput {
  data: {
    chatid: string
  }
}
