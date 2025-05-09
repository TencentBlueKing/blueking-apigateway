export default class RequestError extends Error {
  public code: number; // 错误代码
  public message: string; // 错误信息
  public response: any; // 可选的响应对象

  /**
   * 构造函数
   * @param code 错误代码
   * @param message 错误信息
   * @param response 可选的响应对象
   */
  constructor(code: number, message: string, response?: any) {
    super();
    this.code = code;
    this.message = message;
    this.response = response;
  }
}
