# Generated manually

from django.db import migrations


def create_default_categories(apps, schema_editor):
    """创建默认分类"""
    MCPServerCategory = apps.get_model('mcp_server', 'MCPServerCategory')

    # 默认分类数据
    # name 字段为英文标识，用于程序判断；display_name 为中文显示名称
    default_categories = [
        {
            'name': 'Official',
            'display_name': '官方',
            'description': '官方提供的 MCP Server',
            'sort_order': 1,
        },
        {
            'name': 'Featured',
            'display_name': '精选',
            'description': '精选推荐的 MCP Server',
            'sort_order': 2,
        },
        {
            'name': 'DevOps',
            'display_name': '运维工具',
            'description': '运维相关的工具和服务',
            'sort_order': 3,
        },
        {
            'name': 'Monitoring',
            'display_name': '监控告警',
            'description': '监控和告警相关的工具',
            'sort_order': 4,
        },
        {
            'name': 'ConfigManagement',
            'display_name': '配置管理',
            'description': '配置管理相关的工具',
            'sort_order': 5,
        },
        {
            'name': 'DevTools',
            'display_name': '开发工具',
            'description': '开发相关的工具和服务',
            'sort_order': 6,
        },
        {
            'name': 'OfficeApps',
            'display_name': '办公应用',
            'description': '办公相关的应用和工具',
            'sort_order': 7,
        },
        {
            'name': 'OperationSupport',
            'display_name': '运营支持',
            'description': '运营支持相关的工具',
            'sort_order': 8,
        },
    ]

    for category_data in default_categories:
        MCPServerCategory.objects.get_or_create(
            name=category_data['name'],
            defaults=category_data
        )


def reverse_create_default_categories(apps, schema_editor):
    """删除默认分类（仅删除本迁移中创建的分类，避免误删用户自定义分类）"""
    MCPServerCategory = apps.get_model('mcp_server', 'MCPServerCategory')
    default_category_names = [
        'Official',
        'Featured',
        'DevOps',
        'Monitoring',
        'ConfigManagement',
        'DevTools',
        'OfficeApps',
        'OperationSupport',
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