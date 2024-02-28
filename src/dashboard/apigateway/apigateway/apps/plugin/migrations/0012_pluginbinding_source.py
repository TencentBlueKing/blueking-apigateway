# Generated by Django 3.2.18 on 2024-02-28 07:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plugin', '0011_plugintype_scope'),
    ]

    operations = [
        migrations.AddField(
            model_name='pluginbinding',
            name='source',
            field=models.CharField(choices=[('yalm_import', 'yalm导入'), ('user_create', '用户创建')], default='user_create', max_length=32, null=True),
        ),
    ]
