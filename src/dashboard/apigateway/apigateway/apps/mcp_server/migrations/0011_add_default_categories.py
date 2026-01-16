# Generated manually

from django.db import migrations


def create_default_categories(apps, schema_editor):
    """创建默认分类"""
    MCPServerCategory = apps.get_model('mcp_server', 'MCPServerCategory')
    
    default_categories = [
        {
            'name': 'official',
            'display_name': '官方',
            'description': '官方提供的 MCP Server',
            'type': 'official',
            'sort_order': 1,
        },
        {
            'name': 'featured',
            'display_name': '精选',
            'description': '精选推荐的 MCP Server',
            'type': 'featured',
            'sort_order': 2,
        },
        {
            'name': 'devops',
            'display_name': '运维工具',
            'description': '运维相关的工具和服务',
            'type': 'devops',
            'sort_order': 3,
        },
        {
            'name': 'monitoring',
            'display_name': '监控告警',
            'description': '监控和告警相关的工具',
            'type': 'monitoring',
            'sort_order': 4,
        },
        {
            'name': 'config_management',
            'display_name': '配置管理',
            'description': '配置管理相关的工具',
            'type': 'config_management',
            'sort_order': 5,
        },
        {
            'name': 'dev_tools',
            'display_name': '开发工具',
            'description': '开发相关的工具和服务',
            'type': 'dev_tools',
            'sort_order': 6,
        },
        {
            'name': 'office_apps',
            'display_name': '办公应用',
            'description': '办公相关的应用和工具',
            'type': 'office_apps',
            'sort_order': 7,
        },
        {
            'name': 'operation_support',
            'display_name': '运营支持',
            'description': '运营支持相关的工具',
            'type': 'operation_support',
            'sort_order': 8,
        },
    ]
    
    for category_data in default_categories:
        MCPServerCategory.objects.get_or_create(
            name=category_data['name'],
            defaults=category_data
        )


def reverse_create_default_categories(apps, schema_editor):
    """删除默认分类"""
    MCPServerCategory = apps.get_model('mcp_server', 'MCPServerCategory')
    MCPServerCategory.objects.all().delete()


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