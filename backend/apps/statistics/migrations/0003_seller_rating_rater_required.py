from django.db import migrations, models


def drop_null_rater_rows(apps, schema_editor):
    SellerRating = apps.get_model('statistics', 'SellerRating')
    SellerRating.objects.filter(rater__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('statistics', '0002_alter_sellerrating_score'),
    ]

    operations = [
        migrations.RunPython(drop_null_rater_rows, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='sellerrating',
            name='rater',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='given_ratings', to='users.user'),
        ),
    ]
