# Generated by Django 2.2.9 on 2021-04-05 02:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0013_comment_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='image',
        ),
        migrations.RemoveField(
            model_name='post',
            name='image',
        ),
    ]