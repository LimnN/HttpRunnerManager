# Generated by Django 2.2 on 2019-04-09 16:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ApiManager', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='XmindCase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('name', models.CharField(max_length=256)),
                ('belong_project', models.CharField(max_length=50, verbose_name='所属项目')),
                ('suite', models.CharField(max_length=100, verbose_name='所属模块')),
                ('belong_module', models.CharField(max_length=100, verbose_name='功能子模块')),
                ('steps', models.TextField(verbose_name='步骤')),
                ('attributes', models.CharField(max_length=100, verbose_name='属性')),
                ('author', models.IntegerField(verbose_name='创建用户')),
                ('file_name', models.CharField(max_length=256, verbose_name='filename')),
                ('xmind_file', models.FileField(max_length=256, upload_to='', verbose_name='xmind')),
                ('xlsx_file', models.FileField(max_length=256, upload_to='', verbose_name='xlsx')),
            ],
            options={
                'verbose_name': 'Xmind用例',
                'db_table': 'XmindCases',
            },
        ),
    ]
