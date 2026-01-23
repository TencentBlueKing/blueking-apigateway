# Generated manually

from django.db import migrations


def create_default_categories(apps, schema_editor):
    """创建默认分类"""
    MCPServerCategory = apps.get_model('mcp_server', 'MCPServerCategory')

    # 默认分类数据
    # name 字段为英文标识，用于程序判断；display_name 为中文显示名称
    default_categories = [
        {
            'name': 'Uncategorized',
            'display_name': '未分类',
            'description': '未设置分类的 MCP Server',
            'sort_order': 1,
        },
        {
            'name': 'Official',
            'display_name': '官方资源',
            'description': '蓝鲸官方提供的SRE工具链',
            'sort_order': 2,
        },
        {
            'name': 'Featured',
            'display_name': '精选推荐',
            'description': '专家精选的SRE效能工具',
            'sort_order': 3,
        },
        {
            'name': 'Monitoring',
            'display_name': '监控告警',
            'description': '基础设施与应用性能监控工具',
            'sort_order': 4,
        },
        {
            'name': 'ConfigManagement',
            'display_name': '配置管理',
            'description': '基础设施即代码(IaC)与配置管理',
            'sort_order': 5,
        },
        {
            'name': 'DevOps',
            'display_name': '持续交付',
            'description': 'CI/CD流水线与发布管理工具',
            'sort_order': 6,
        },
        {
            'name': 'Emergency',
            'display_name': '故障管理',
            'description': '应急响应、故障自愈与事故处理平台',
            'sort_order': 7,
        },
        {
            'name': 'Database',
            'display_name': '数据服务',
            'description': '数据库管理、备份与SQL审核工具',
            'sort_order': 8,
        },
        {
            'name': 'Automation',
            'display_name': '运维自动化',
            'description': '作业调度、批量操作与自动化编排',
            'sort_order': 9,
        },
        {
            'name': 'Observability',
            'display_name': '可观测性',
            'description': '日志分析、链路追踪与指标聚合平台',
            'sort_order': 10,
        },
        {
            'name': 'Security',
            'display_name': '安全合规',
            'description': '合规审计、漏洞扫描与访问控制系统',
            'sort_order': 11,
        },
        {
            'name': 'ResourceOptimize',
            'display_name': '资源优化',
            'description': '成本管理、容量规划与资源调度工具',
            'sort_order': 12,
        },
        {
            'name': 'ChaosEngineering',
            'display_name': '混沌工程',
            'description': '故障注入、韧性测试与容错验证工具',
            'sort_order': 13,
        },
        {
            'name': 'Network',
            'display_name': '网络管理',
            'description': '网络监控、配置与流量分析工具',
            'sort_order': 14,
        },
    ]

    for category_data in default_categories:
        MCPServerCategory.objects.get_or_create(
            name=category_data['name'],
            defaults=category_data
        )

    # 将现有没有分类的 MCPServer 关联到"未分类"
    MCPServer = apps.get_model('mcp_server', 'MCPServer')
    uncategorized = MCPServerCategory.objects.filter(name='Uncategorized').first()
    if uncategorized:
        # 获取所有没有分类的 MCPServer
        servers_without_category = MCPServer.objects.filter(categories__isnull=True)
        for server in servers_without_category:
            server.categories.add(uncategorized)


def reverse_create_default_categories(apps, schema_editor):
    """删除默认分类（仅删除本迁移中创建的分类，避免误删用户自定义分类）"""
    MCPServerCategory = apps.get_model('mcp_server', 'MCPServerCategory')
    default_category_names = [
        'Uncategorized',
        'Official',
        'Featured',
        'Monitoring',
        'ConfigManagement',
        'DevOps',
        'Emergency',
        'Database',
        'Automation',
        'Observability',
        'Security',
        'ResourceOptimize',
        'ChaosEngineering',
        'Network',
    ]
    MCPServerCategory.objects.filter(name__in=default_category_names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('mcp_server', '0010_add_mcp_server_category'),
    ]

    operations = [
        migrations.RunPython(
            create_default_categories,
            reverse_create_default_categories,
        ),
    ]