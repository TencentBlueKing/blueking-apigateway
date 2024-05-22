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