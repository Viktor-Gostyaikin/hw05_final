# Generated by Django 2.2.9 on 2021-04-04 01:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0010_post_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='image',
        ),
    ]
