from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('textbooks', '0009_resourceorder_cancel_by_role_and_reason_choices'),
    ]

    operations = [
        migrations.CreateModel(
            name='TextbookRating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.PositiveSmallIntegerField(verbose_name='评分')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('textbook', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='ratings', to='textbooks.textbook', verbose_name='教材')),
                ('user', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='textbook_ratings', to='users.user', verbose_name='用户')),
            ],
            options={
                'verbose_name': '教材评分',
                'verbose_name_plural': '教材评分',
                'db_table': 'textbook_ratings',
                'unique_together': {('textbook', 'user')},
            },
        ),
    ]
