# Generated by Django 4.2.8 on 2024-10-25 22:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("test_app", "0014_nestedchild"),
    ]

    operations = [
        migrations.AddField(
            model_name="childclass",
            name="active",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="modelwithparentresource",
            name="active",
            field=models.BooleanField(default=True),
        ),
    ]