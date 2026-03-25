from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_order_started_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='cancel_reason',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='取消原因'),
        ),
    ]
