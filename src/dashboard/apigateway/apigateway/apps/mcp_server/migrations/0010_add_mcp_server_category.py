# Generated manually

from django.db import migrations, models
import django.db.models.deletion
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ('mcp_server', '0009_alter_mcpserver_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='MCPServerCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_time', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_time', models.DateTimeField(auto_now=True, null=True)),
                ('created_by', models.CharField(blank=True, max_length=32, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=32, null=True)),
                ('name', models.CharField(help_text='分类名称', max_length=64, unique=True)),
                ('display_name', models.CharField(help_text='分类显示名称', max_length=128)),
                ('description', models.TextField(blank=True, default='', help_text='分类描述')),
                ('type', models.CharField(
                    choices=[
                        ('official', '官方'),
                        ('featured', '精选'),
                        ('devops', '运维工具'),
                        ('monitoring', '监控告警'),
                        ('config_management', '配置管理'),
                        ('dev_tools', '开发工具'),
                        ('office_apps', '办公应用'),
                        ('operation_support', '运营支持'),
                    ],
                    help_text='分类类型',
                    max_length=32,
                )),
                ('is_active', models.BooleanField(default=True, help_text='是否启用')),
                ('sort_order', models.IntegerField(default=0, help_text='排序顺序，数字越小越靠前')),
            ],
            options={
                'verbose_name': 'MCPServer 分类',
                'verbose_name_plural': 'MCPServer 分类',
                'db_table': 'mcp_server_category',
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.AddField(
            model_name='mcpserver',
            name='categories',
            field=models.ManyToManyField(
                blank=True,
                help_text='MCPServer 所属分类',
                related_name='mcp_servers',
                to='mcp_server.MCPServerCategory',
            ),
        ),
    ]