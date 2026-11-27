export interface IMCPServerTimeQuery {
  /** Unix 秒。time_start 和 time_end 成对传入，或改用 time_range。 */
  time_start?: number
  time_end?: number
  time_range?: number
}
