export default class RequestError extends Error {
  code: number | string;
  message: string;
  response: any;
  constructor(code: number | string, message: string, response?: any) {
    super();
    this.code = code;
    this.message = message;
    this.response = response;
  }
}
