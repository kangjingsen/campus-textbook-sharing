from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('textbooks', '0007_resourceorder_payment_qr_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourceorder',
            name='cancel_reason',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='取消原因'),
        ),
    ]
