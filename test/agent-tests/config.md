# Agent Test Suite Configuration

## Paths

**Cases Path**: test/agent-tests/cases/
**Reports Path**: test/agent-tests/reports/

## Usage

All connection parameters are passed as skill arguments:

```
/agent-test run --url <URL> --user <USERNAME> --password <PASSWORD>
/agent-test run --url <URL> --cookie <COOKIE_VALUE>
/agent-test generate --url <PAGE_URL> --user <USERNAME> --password <PASSWORD>
```

## Login Flow Details (Validated 2026-03-25)

The login page has TWO possible forms depending on context:

**Form A (Chinese — most common):**
1. Navigate to the target URL → redirects to login page
2. Username field: `#user` (placeholder "请输入用户名")
3. Password field: `#password` (placeholder "请输入密码")
4. Submit: `.login-btn` (text "立即登录")
5. Use `.type()` not `.fill()` for password (special chars like `$`, `&`, `%`)

**Form B (English — sometimes appears):**
1. Username field: textbox "Please enter your username"
2. Password field: textbox "Please enter your password"
3. Submit: button "Log in"

After successful login → redirects back to dashboard.
Dashboard shows: "新建网关" button, gateway list table with columns: 网关名, 创建者, 环境列表, 运营状态, 资源数量, 操作

## Alternative: Cookie-Based Auth

If automated login is blocked (captcha, rate limiting), provide a session cookie directly via `--cookie`.
Set cookies on the target domain — the login sets cookies on the parent domain.
