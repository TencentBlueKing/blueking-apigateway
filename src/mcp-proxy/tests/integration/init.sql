-- 初始化测试数据库
-- 创建必要的表结构（简化版，用于集成测试）

-- 网关表 (实际表名是 core_api)
CREATE TABLE IF NOT EXISTS `core_api` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `name` varchar(64) NOT NULL,
    `description` varchar(512) DEFAULT '',
    `status` int(11) NOT NULL DEFAULT 1,
    `is_public` tinyint(1) NOT NULL DEFAULT 0,
    `created_time` datetime(6) NOT NULL,
    `updated_time` datetime(6) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 环境表
CREATE TABLE IF NOT EXISTS `core_stage` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `api_id` int(11) NOT NULL,
    `name` varchar(64) NOT NULL,
    `description` varchar(512) DEFAULT '',
    `status` int(11) NOT NULL DEFAULT 1,
    `created_time` datetime(6) NOT NULL,
    `updated_time` datetime(6) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `api_id_name` (`api_id`, `name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- JWT 密钥表
CREATE TABLE IF NOT EXISTS `core_jwt` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `api_id` int(11) NOT NULL,
    `public_key` text NOT NULL,
    `private_key` text NOT NULL,
    `encrypted_private_key` text,
    `created_time` datetime(6) NOT NULL,
    `updated_time` datetime(6) NOT NULL,
    PRIMARY KEY (`id`),
    KEY `idx_api_id` (`api_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 资源版本表
CREATE TABLE IF NOT EXISTS `core_resource_version` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `api_id` int(11) NOT NULL,
    `version` varchar(128) NOT NULL,
    `schema_version` varchar(32) DEFAULT '1.0',
    `data` longtext,
    `created_time` datetime(6) NOT NULL,
    `updated_time` datetime(6) NOT NULL,
    PRIMARY KEY (`id`),
    KEY `idx_api_id` (`api_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 发布表
CREATE TABLE IF NOT EXISTS `core_release` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `api_id` int(11) NOT NULL,
    `stage_id` int(11) NOT NULL,
    `resource_version_id` int(11) NOT NULL,
    `created_time` datetime(6) NOT NULL,
    `updated_time` datetime(6) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `stage_id` (`stage_id`),
    KEY `idx_api_stage` (`api_id`, `stage_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- OpenAPI 规范表
CREATE TABLE IF NOT EXISTS `openapi_gateway_resource_version_spec` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `api_id` int(11) NOT NULL,
    `resource_version_id` int(11) NOT NULL,
    `schema` longtext NOT NULL,
    `created_time` datetime(6) NOT NULL,
    `updated_time` datetime(6) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `resource_version_id` (`resource_version_id`),
    KEY `idx_api_id` (`api_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- MCP Server 表
CREATE TABLE IF NOT EXISTS `mcp_server` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `name` varchar(128) NOT NULL,
    `description` varchar(512) DEFAULT '',
    `is_public` tinyint(1) NOT NULL DEFAULT 0,
    `labels` text,
    `resource_names` text,
    `gateway_id` int(11) NOT NULL,
    `stage_id` int(11) NOT NULL,
    `protocol_type` varchar(32) DEFAULT 'sse',
    `status` int(11) NOT NULL DEFAULT 1,
    `created_time` datetime(6) NOT NULL,
    `updated_time` datetime(6) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- MCP Server 扩展表 (用于存储 Prompts 等)
CREATE TABLE IF NOT EXISTS `mcp_server_extend` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `mcp_server_id` int(11) NOT NULL,
    `type` varchar(32) NOT NULL,
    `content` longtext NOT NULL,
    `created_by` varchar(32) DEFAULT '',
    `updated_by` varchar(32) DEFAULT '',
    `created_time` datetime(6) NOT NULL,
    `updated_time` datetime(6) NOT NULL,
    PRIMARY KEY (`id`),
    KEY `idx_mcp_server_id` (`mcp_server_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- MCP Server 应用权限表
CREATE TABLE IF NOT EXISTS `mcp_server_app_permission` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `mcp_server_id` int(11) NOT NULL,
    `bk_app_code` varchar(64) NOT NULL,
    `grant_type` varchar(32) NOT NULL,
    `expires` datetime(6),
    `created_time` datetime(6) NOT NULL,
    `updated_time` datetime(6) NOT NULL,
    PRIMARY KEY (`id`),
    KEY `idx_mcp_server_id` (`mcp_server_id`),
    KEY `idx_bk_app_code` (`bk_app_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==================== 插入测试数据 ====================

-- 网关 (必须使用 bk-apigateway 名称，因为 JWT 验证使用此名称)
INSERT INTO `core_api` (`id`, `name`, `description`, `status`, `is_public`, `created_time`, `updated_time`)
VALUES (1, 'bk-apigateway', 'Official API Gateway for Integration Tests', 1, 1, NOW(), NOW());

-- 环境
INSERT INTO `core_stage` (`id`, `api_id`, `name`, `description`, `status`, `created_time`, `updated_time`)
VALUES (1, 1, 'prod', 'Production Stage', 1, NOW(), NOW());

-- JWT 密钥对 (使用统一的公钥和加密后的私钥)
INSERT INTO `core_jwt` (`id`, `api_id`, `public_key`, `private_key`, `encrypted_private_key`, `created_time`, `updated_time`)
VALUES (1, 1, 
'-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvQ6orKLTfKKcOBkfenRJ
vDO6NinGW7z6A+IWe7N3eBnkpOzmBUGQdtyfDGfMo8RA5FNKFBSS6Wrq1hhTpSkm
M/OJL54mPDOcx9h9MFtmE+6/YrXlvyhmG7DLgr6NwEUYVVre44ZTNA1A5z/OoFXM
C9Ama8uEUcScWgUSU7Mwj6sHhbrU6pZA4JFMgnz/s/vmLg2exX+Yl332ZtHilF/V
aLpsrUJ1iQqfWShYvjowXOrMNfRWyJJrI6YoNogHvM/Z/67fttXvPOTQcE8tTKCV
saoRETM7i/CohGsME8013x9l56IrRq1Gp/4jKoQStbfm7SMjQ5cPWespppDhNJrU
CwIDAQAB
-----END PUBLIC KEY-----',
'',
'fb635e8543dde12366bfa92ef24fbf82957b0610faabeb4ad5e55e1168177f30340739a37e757f671519df5cdf222f2d3362d5db50c9c26fc77c611389fe595aa00aea35dff9f074bb832bc80fcc92588d2c7987333081afea49f556106545733ad8e0076205dfa5dfb295b8e8cbff8d5c9fe3613cc06a9b46f7a20040304b8172c8bf632ea7323b0e249cae066d969e5c2d804325f6be787973f983f4b6dfbfa7dafb0ee70d1f2d62fd1621e6ec828c6386945b8a4106739368db32be0b0cfbe8f4b041e2410ddfd5f35025774b072b12393a4fd8495dbfb3dacc815d1ae1669b410e8610a8e365c7237079aeac94514a9cf77114c6d52349ff58696c7b3c35830b8f9b281532d74bf203e973fbe3791446006a7690e1fbab411c375a977298e4d5bda0d256ad8377a32ad637b256d0727a8862ea733c2cfe9b71ef17d85950efca942a47d98ca45ba030ed79ad6239042000f4806f1b5b82dea74efe66758584000af6291f02cec2a5d3c6e9d0d544c8dedd07a75f09268cf3e55c8d9e1cc21100de4612959ce8052fb3b6b42ba295ac956ca091f804d18cd8e333c3192dbb65f6654afaa7d280185ce596dafb2b08a0d3b2d92c035fce00c6e39bb49da71e7bd0116fa81453c497e5b17e511fd439db2511fddfe105eaa0ca6628d384cad886d69f0be8aedba48b4e550b3b206c55002ab17713086717cb9da98ba13698a24b6043a4451ec7fae070435f600184528ac3049a73c8da7a15856b7f6117859636ea97d58cdf8fefe2197cbe1de917325670b71dc2fccaa58ed220676a89f90342fb6579cde472440108c45c6b058652e7dfd895ccf651820bf41a2eb7c418abb816171868d15a7df1fa829d02d810fc5dfce4edd23792430aafa993ccc412e6a5acf412db47976fd00e9f19935e23472fe6f0f7c06a598947a5b572ead217c71b9cad74c6d965720e419e5ea771905e2bf7b7e3cd517bc3138c10755797ad1c2ed29904aef76b3c8cb773f2fa1be288685ab01171a3196459810bd9a4153def1a00dc914620b2cfdcf2d3a134e93b415aae2e733e7dff9b3fc95cd111cee41617b08798983b9b7e399d4a03e836230e7bb8d4b107dd8d3f75737daa9fac94fca20345d04d9043ad737b1c96d39f2b26937406a61c50b470c5a48973be7da9b5a59a2b4f444a91a0e76cdfaccf2902a792824664dcff12234b2e0cd4d05586eadc2d6b0f7c6e9d5f757a90fec55d1b689ee85bdfd03f900ae577953383cab48b357f21fd342a6109cc4202a21b1dffa20269886f23e22d2c4bce26cfb2a2c8ca251f86324a719d664b1a9b13d9e2ec88ee52d6668f80ec88378d5d3c5bdf48fcab5de1202f7b259da30e41efc054241d5e325a2306175db20674a2b98fbfd6a430462196fa950fbcb062ea9fd55f5b87677c2be5ba0d277adfc027b95d4efc9c22c9a660085d01585b1ddb6c2b071d730b69d55c010005e47b897ef6fe57051bb28031f702c3258959b4eb2fbd08b0c4c66a6088d14448c78ca0f7657c3012c8b4b209e605528dc9855ec183cff45f35d7ff6575ae784cadac34ad3f440391fdf945fbb305deffb64507c4d073bf0e07c0f6047d5bd98eb751550d62f75dcb791406b24a0b37ed84a12a27f6118d82f936f91aa59196ad39a0b34cc18079312bd89083065d9ea97abee142fc969a237c508f32b82a169779621f2527a7facdac8a091cc95e451b403b1b0fa55c0233e424a089c606bad159d01a31c9168aceadaae6736d4c98d43890137bac56632fcad19300dd2d70ba528a6645f62471001acb38be5b066c964ad38d960e248a773c87f0132f896241cd9e1ddb62b99a9387029022acf4d63b3210cab6f7aa5fb73d0e5fa3b9fecaeb288dd777fa279a3af87b8026c77a6bad455ab6697966464dc2acea73e25fbac3492c990734ba22d370ce8db71a44ff6e8dd341e6fe4b5ca04110c67d3456eeff1e5f20a08b0e4ffae08a452e6664486c7536aebce1a18af966ac0d9cd80d372ce2001b10e40f4d79614138f258ddb109fcd62a5e37481503b7e746efd1278f31a43bdc694cc6efac78bfc4448b5e370baabc38d6da1f139a713ca47d4b872d5c418de926884866285d619ae4863f78cf673dffca4224b10d6a12fb18d2871daffb8f5fed67c9df62bde5806f7961ea928bad3889f17cf329038a9eecc9813fb61cd77e8c5fb3229514e7b6c55d4c14da58e37df81b23a6cc6aedc650c882719ef0116adf1c385c6774e6f0c8eb502dd125e875316f17af6c3c1c510c2c0b8d680c054362064b8c15e941761751a076bc3dfaa20755c437573a4fab2b297c426acc91dea9bd3fd6a0d38ea3377c2276131f5a891adc777a8097e66b9af9e8c7c037a2046821decf',
NOW(), NOW());

-- 资源版本
INSERT INTO `core_resource_version` (`id`, `api_id`, `version`, `schema_version`, `data`, `created_time`, `updated_time`)
VALUES (1, 1, '1.0.0', '1.0', '{}', NOW(), NOW());

-- 发布记录 (关联网关、环境和资源版本)
INSERT INTO `core_release` (`id`, `api_id`, `stage_id`, `resource_version_id`, `created_time`, `updated_time`)
VALUES (1, 1, 1, 1, NOW(), NOW());

-- OpenAPI 规范 (定义 echo 和 ping 工具，使用 go-httpbin 的 /anything 端点)
INSERT INTO `openapi_gateway_resource_version_spec` (`id`, `api_id`, `resource_version_id`, `schema`, `created_time`, `updated_time`)
VALUES (1, 1, 1, '{
  "openapi": "3.0.3",
  "info": {
    "title": "Test API Gateway",
    "description": "Test API for integration testing",
    "version": "1.0.0"
  },
  "servers": [
    {
      "url": "http://localhost:8080/api/test-gateway/prod"
    }
  ],
  "paths": {
    "/anything/echo": {
      "post": {
        "operationId": "echo",
        "summary": "Echo message",
        "description": "Returns the message that was sent (uses go-httpbin /anything endpoint)",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "message": {
                    "type": "string",
                    "description": "The message to echo back"
                  }
                },
                "required": ["message"]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Successful response",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "json": {
                      "type": "object",
                      "description": "The JSON body that was sent"
                    }
                  }
                }
              }
            }
          }
        }
      }
    },
    "/anything/ping": {
      "get": {
        "operationId": "ping",
        "summary": "Ping service",
        "description": "Check if the service is alive (uses go-httpbin /anything endpoint)",
        "responses": {
          "200": {
            "description": "Successful response",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "method": {
                      "type": "string"
                    },
                    "url": {
                      "type": "string"
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}', NOW(), NOW());

-- 测试用 MCP Server (SSE 协议)
-- resource_names 使用分号分隔
INSERT INTO `mcp_server` (`id`, `name`, `description`, `is_public`, `labels`, `resource_names`, `gateway_id`, `stage_id`, `protocol_type`, `status`, `created_time`, `updated_time`)
VALUES (1, 'test-sse-server', 'Test SSE MCP Server', 1, '', 'echo;ping', 1, 1, 'sse', 1, NOW(), NOW());

-- 测试用 MCP Server (Streamable HTTP 协议)
INSERT INTO `mcp_server` (`id`, `name`, `description`, `is_public`, `labels`, `resource_names`, `gateway_id`, `stage_id`, `protocol_type`, `status`, `created_time`, `updated_time`)
VALUES (2, 'test-http-server', 'Test HTTP MCP Server', 1, '', 'echo;ping', 1, 1, 'streamable_http', 1, NOW(), NOW());

-- 测试用 Prompts (存储在 mcp_server_extend 表)
INSERT INTO `mcp_server_extend` (`id`, `mcp_server_id`, `type`, `content`, `created_by`, `updated_by`, `created_time`, `updated_time`)
VALUES (1, 1, 'prompts', '[{"id":1,"name":"Test Prompt","code":"test-prompt","content":"This is a test prompt for integration testing.","labels":[],"is_public":true,"space_code":"","space_name":""}]', 'admin', 'admin', NOW(), NOW());

-- 为 HTTP Server 也添加 Prompts
INSERT INTO `mcp_server_extend` (`id`, `mcp_server_id`, `type`, `content`, `created_by`, `updated_by`, `created_time`, `updated_time`)
VALUES (2, 2, 'prompts', '[{"id":2,"name":"HTTP Test Prompt","code":"http-test-prompt","content":"This is a test prompt for HTTP MCP server.","labels":[],"is_public":true,"space_code":"","space_name":""}]', 'admin', 'admin', NOW(), NOW());

-- 应用权限 (允许 test-app 访问 MCP Server)
INSERT INTO `mcp_server_app_permission` (`id`, `mcp_server_id`, `bk_app_code`, `grant_type`, `expires`, `created_time`, `updated_time`)
VALUES (1, 1, 'test-app', 'grant', '2099-12-31 23:59:59', NOW(), NOW());

INSERT INTO `mcp_server_app_permission` (`id`, `mcp_server_id`, `bk_app_code`, `grant_type`, `expires`, `created_time`, `updated_time`)
VALUES (2, 2, 'test-app', 'grant', '2099-12-31 23:59:59', NOW(), NOW());
