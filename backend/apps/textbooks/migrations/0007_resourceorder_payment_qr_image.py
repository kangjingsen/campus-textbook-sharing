from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('textbooks', '0006_resourceorder_status_max_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourceorder',
            name='payment_qr_image',
            field=models.ImageField(blank=True, null=True, upload_to='payment_qr/', verbose_name='支付二维码图片'),
        ),
    ]
