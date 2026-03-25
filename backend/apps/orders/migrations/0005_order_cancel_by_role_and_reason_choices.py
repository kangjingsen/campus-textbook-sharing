from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_order_cancel_reason'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='cancel_reason',
            field=models.CharField(blank=True, choices=[('price', '价格不合适'), ('schedule', '无法线下交易'), ('duplicate', '重复下单'), ('not_needed', '暂时不需要'), ('unresponsive', '对方长时间未响应'), ('other', '其他')], default='', max_length=20, verbose_name='取消原因'),
        ),
        migrations.AddField(
            model_name='order',
            name='cancel_by_role',
            field=models.CharField(blank=True, choices=[('buyer', '买家'), ('seller', '卖家'), ('system', '系统')], default='', max_length=10, verbose_name='取消发起方'),
        ),
    ]
