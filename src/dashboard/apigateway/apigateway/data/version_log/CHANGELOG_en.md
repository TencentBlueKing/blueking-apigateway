<!-- 2024-08-05 -->
# V1.14.0 Release Log

### Bug Fixes

- Plugins: Header transformation validates duplicate headers
- Incorrect frontend request URL when the notification center is activated
- Maintenance staff information not displaying correctly in basic information
- After a successful release, the current environment's version number is updated to prevent page functionality issues in case of release failure
- Issue with negative duration displayed during the release process

### Feature Enhancements

- Import and export enhancements: support for openapi 3.0
- Improved user experience on the log search page
- Enhanced online debugging experience
- Basic information: support for configuring related_apps
- Plugins: Header transformation supports settings that include the `$` symbol

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

### Feature Enhancements

- Online debugging apps are no longer displayed on the permission list page
- Global configuration support for BK_SHARED_RES_URL

---

<!-- 2024-06-12 -->
# V1.13.5 Release Log

### Feature Enhancements

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

### Feature Enhancements

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

### Feature Enhancements

- Added detection for releases before version 1.13, prompting users to upgrade to the new version
- Added environment variables BK_APP_CODE and BK_REPO_URL to dashboard-fe

---

<!-- 2024-05-27 -->
# V1.13.2 Release Log

### Bug Fixes

- Fixed frontend issues

### Feature Enhancements

- Added is_from_logout parameter to logout

---

<!-- 2024-05-22 -->
# V1.13.1 Version Update Log

### Bug Fixes

- fix: stage plugins can't be edited
- fix: menu i18n issue

### Feature Enhancements

- Stage resource list is too large to display

---

<!-- 2024-05-20 -->
# V1.13.0 Version Update Log

### Bug Fixes

### Feature Enhancements

- Refactored backend code for protocol standardization
- Brand new product page

---

<!-- 2024-01-24 -->
# V1.12.16 Version Update Log

### Bug Fixes

- Fixed a problem where the esb component could not synchronize successfully (upgraded esb to 2.14.65)
- Hidden bk-header-rewrite plugin configuration

### Feature Enhancements

- Upgraded bk-esb to 2.14.64, including monitoring and bklog changes
- Added validation: gateway_name/stage_name/resource_name cannot end with `-` or `_`

---

<!-- 2023-12-28 -->
# V1.12.14 Version Update Log

### Bug Fixes

- Fixed checking for resource_perm_required before checking verified_app_required = True
- Open API sync stage does not trigger release, allows environment variables to be absent in the gateway

### Feature Enhancements

- Upgraded esb to 2.14.61
- When querying existing permissions of an application, display the status of permissions being applied for
- Check the permissions of an application accessing gateway resources, and send notifications to the application owner if they are about to expire
- In the alarm information, removed the querystring
- Statistics: Support pulling request volume data by gateway

---

<!-- 2023-11-08 -->
# V1.12.9 Version Update Log

### Bug Fixes

- Fixed: PluginConfigManager missing method bulk_delete
- Fixed: operator diff not taking effect
- Fixed: an issue where apisix DNS resolution failure could not be recovered

### Feature Enhancements

- API documentation added bk_token description
- apisix supports graceful shutdown
- Optimization of apisix rebuild radixtree
- Gateway supports configuration for developers

---

<!-- 2023-09-25 -->
# V1.12.1 Version Update Log

> Official outgoing version

### Bug Fixes

- fix: operator remove duplicated items bug
- fix: operator full sync bug
- fix: apisix online issues
- fix: front-end interaction issues
- fix: when requesting an exception on the backend interface, the results will not be cached