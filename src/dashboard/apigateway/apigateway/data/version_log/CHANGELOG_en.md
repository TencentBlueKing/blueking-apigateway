<!-- 2025-04-18 -->
# V1.15.5 Release Log

### Features

- Support using tls to connect MySQL and Redis

---

<!-- 2025-04-08 -->
# V1.15.4 Release Log

### Bug Fixes

- Fix: Backend service resource query error
- Fix: Incorrect tooltips content in one-click group pull
- Fix: Incorrect number of resource changes displayed when generating versions
- Backport: Fix issues reported after 1.15上线
- Fix: celery stuck in some environments

### Features

- v2 sync api: list permissions

---

<!-- 2025-02-17 -->
# V1.15.3 Release Log

### Bug Fixes

- Fix: Some frontend issues

---

<!-- 2025-02-12 -->
# V1.15.2 Release Log

### Bug Fixes

- Fix: Unable to use the same key for filtering in transaction logs
- Fix: Comparison failure when creating resource versions
- Fix: Outdated resource versions could still be published
- Fix: Display issues in component API documentation
- Fix: API documentation links directly to the API
- Fix: Icon and logo display errors in the version release process
- Fix: Page height error when release notifications appear
- Fix: Bulk modification of resource documents in resource import table
- Fix: Add Golang option when viewing SDK
- Fix: Height of resource configuration drawer
- Fix: Issue with repeated clicking of the online debug button
- Fix: Unable to view entire value when environment management variable is too long
- Fix: Unit error in statistical charts
- Fix: Naming conflict caused by using both underscores and camel case in resource names, added pre-validation
- Fix: Added DASHBOARD_CSRF_TRUSTED_ORIGINS
- Fix: Incomplete display of the list when plugins exceed 10 items

---

<!-- 2024-11-29 -->
# V1.15.1 Release Log

### Bug Fixes

- Fix: Compatibility with MySQL 5.7

---

<!-- 2024-11-15 -->
# V1.15.0 Release Log

### Features

- Data Operation - Statistical Report: Complete page redesign.
- Permission Management - Application Permissions: Full page redesign, merging two permission dimensions into a single list page/export.
- Gateway/Component API Documentation and Gateway/Component SDK: Merged into a single page, API Documentation, with all functions needing testing.
- Optimized Log Query Page: Search history/icon selection to narrow scope.
- Optimized Online Debugging Page.
- Resource Version: Support for generating Java SDK.
- Resource Configuration: Support for enabling WebSocket.
- Added 4 new plugins to Resource Dimension: Mock, Circuit Breaker, Request Validation, and Fault Injection, with functionality needing testing.
- Upgraded the underlying Django framework and all dependency libraries to the latest version.

---

<!-- 2024-10-30 -->
# V1.14.5 Release Log

### Bug Fixes

- Fixed issues on the resource configuration page
  - Incorrect page number after search
  - Resource configuration table height issue
- Fixed issues in pipeline logs
  - Added search history for log queries
  - Syntax error in log queries
  - Data export issue resulting in empty logs
- Fixed issue with header reset when switching in online debugging
- Fixed the issue with resource documentation upload failure
- Fixed backend configuration issues for environment validation during publishing
- Updated bkui to fix XSS vulnerabilities
- Fixed online debugging: refined response status code color differentiation
- Fixed gateway basic information: tooltips for maintenance personnel text
- Optimized resource version comparison display

---

<!-- 2024-10-09 -->
# V1.14.4 Release Log

### Bug Fixes

- Fixed incorrect validation in online debugging

---

<!-- 2024-10-08 -->
# V1.14.3 Release Log

### Bug Fixes

- Fixed the issue where the description disappears when editing a plugin
- Error notification for failed ZIP uploads during document import
- XSS vulnerability fix

---

<!-- 2024-09-26 -->
# V1.14.2 Release Log

### Bug Fixes

- Fixed incorrect official documentation link for resource import
- Added support for delete operation in OpenAPI resource synchronization

---

<!-- 2024-09-25 -->
# V1.14.1 Release Log

### Bug Fixes

- Environment Overview: Resource plugin list merge takes too long
- Fixed issue where a prompt dialog still appears after leaving a page with an edited form

### Features

- Prohibit selecting and publishing schema v1 resource versions
- Standardize documentation center redirect links

---

<!-- 2024-09-13 -->
# V1.14.0 Release Log

### Bug Fixes

- Plugin: Header Rewrite - Validate duplicate headers
- Incorrect frontend request address after enabling the notification center
- Issue with maintenance personnel information not displaying
- After successful publishing, update the associated version number for the current environment to avoid functionality issues on the publish failure page
- Issue with negative time display during the publishing process
- Merge issue for plugin display on the environment overview resource list page
- Disable bk-opentelemetry

### Features

- Optimize import and export configurations to support OpenAPI 3.0
- Optimize log query page
- Optimize online debugging page
- Generate recommended version number when creating a new resource version
- Update the associated version number only after successful version release
- Support configuring associated apps in gateway basic information
- Enable controlled submission of personnel edits in gateway basic information
- Add `bp-` as one of the official built-in gateway prefixes
- Plugin: Add `bk_username` field in `file-logger`
- Plugin: Support `$` for variable retrieval in the "header rewrite" plugin key-value pairs

---

<!-- 2024-08-06 -->
# V1.13.13 Release Log

### Bug Fixes

- Updated title brand name

---

<!-- 2024-08-01 -->
# V1.13.12 Release Log

### Bug Fixes

- Fixed issues with sync_gateway command
- Updated `bk-apigateway` resource version

---

<!-- 2024-08-01 -->
# V1.13.11 Release Log

### Bug Fixes

- Fixed issues with version log internationalization
- Updated gateway API documentation

---

<!-- 2024-07-12 -->
# V1.13.10 Release Log

### Bug Fixes

- Supplemented version logs

---

<!-- 2024-07-12 -->
# V1.13.9 Release Log

### Bug Fixes

- Standardized logout messages
- Supplemented version logs

---

<!-- 2024-06-29 -->
# V1.13.8 Release Log

### Bug Fixes

- Maintenance staff information not displaying correctly in basic information for certain environments

---

<!-- 2024-06-28 -->
# V1.13.7 Release Log

### Bug Fixes

- Maintenance staff information not displaying correctly in basic information for certain environments

---

<!-- 2024-06-21 -->
# V1.13.6 Release Log

### Bug Fixes

- Incorrect frontend request URL when the notification center is activated
- Maintenance staff information not displaying correctly in basic information

### Features

- Online debugging apps are no longer displayed on the permission list page
- Global configuration support for BK_SHARED_RES_URL

---

<!-- 2024-06-12 -->
# V1.13.5 Release Log

### Features

- Changes in backend services to trigger deployment updated to asynchronous

---

<!-- 2024-06-11 -->
# V1.13.4 Release Log

### Bug Fixes

- Fixed issue where maintenance personnel were not displayed in the popup when editing basic information
- Fixed issue with resource list page search not supporting fuzzy search
- Fixed incorrect link in renewal email
- Fixed issue where gateway maximum resource whitelist was ineffective
- Fixed issue in Python SDK where package name contained an extra `-`
- Fixed frontend issues

### Features

- Increased retry attempts for distributed lock release
- Import now supports multiple backends
- Updated plugin descriptions
- Switched public_key retrieval interface to core-api

---

<!-- 2024-05-30 -->
# V1.13.3 Release Log

### Bug Fixes

- Fixed frontend issues
- Fixed eslint issues

### Features

- Added detection for releases before version 1.13, prompting users to upgrade to the new version
- Added environment variables BK_APP_CODE and BK_REPO_URL to dashboard-fe

---

<!-- 2024-05-27 -->
# V1.13.2 Release Log

### Bug Fixes

- Fixed frontend issues

### Features

- Added is_from_logout parameter to logout

---

<!-- 2024-05-22 -->
# V1.13.1 Release Log

### Bug Fixes

- fix: stage plugins can't be edited
- fix: menu i18n issue

### Features

- Stage resource list is too large to display

---

<!-- 2024-05-20 -->
# V1.13.0 Release Log

### Bug Fixes

### Features

- Refactored backend code for protocol standardization
- Brand new product page

---

<!-- 2024-01-24 -->
# V1.12.16 Release Log

### Bug Fixes

- Fixed a problem where the esb component could not synchronize successfully (upgraded esb to 2.14.65)
- Hidden bk-header-rewrite plugin configuration

### Features

- Upgraded bk-esb to 2.14.64, including monitoring and bklog changes
- Added validation: gateway_name/stage_name/resource_name cannot end with `-` or `_`

---

<!-- 2023-12-28 -->
# V1.12.14 Release Log

### Bug Fixes

- Fixed checking for resource_perm_required before checking verified_app_required = True
- Open API sync stage does not trigger release, allows environment variables to be absent in the gateway

### Features

- Upgraded esb to 2.14.61
- When querying existing permissions of an application, display the status of permissions being applied for
- Check the permissions of an application accessing gateway resources, and send notifications to the application owner if they are about to expire
- In the alarm information, removed the querystring
- Statistics: Support pulling request volume data by gateway

---

<!-- 2023-11-08 -->
# V1.12.9 Release Log

### Bug Fixes

- Fixed: PluginConfigManager missing method bulk_delete
- Fixed: operator diff not taking effect
- Fixed: an issue where apisix DNS resolution failure could not be recovered

### Features

- API documentation added bk_token description
- apisix supports graceful shutdown
- Optimization of apisix rebuild radixtree
- Gateway supports configuration for developers

---

<!-- 2023-09-25 -->
# V1.12.1 Release Log

> Official outgoing version

### Bug Fixes

- fix: operator remove duplicated items bug
- fix: operator full sync bug
- fix: apisix online issues
- fix: front-end interaction issues
- fix: when requesting an exception on the backend interface, the results will not be cached