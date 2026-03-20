from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Announcement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='标题')),
                ('summary', models.CharField(blank=True, default='', max_length=300, verbose_name='摘要')),
                ('content', models.TextField(verbose_name='正文')),
                ('is_pinned', models.BooleanField(default=False, verbose_name='置顶')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('published_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='发布时间')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'db_table': 'community_announcements',
                'ordering': ['-is_pinned', '-published_at', '-id'],
            },
        ),
        migrations.CreateModel(
            name='ForumTopic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=220, verbose_name='标题')),
                ('content', models.TextField(verbose_name='内容')),
                ('topic_type', models.CharField(choices=[('discussion', '讨论'), ('question', '问答')], default='discussion', max_length=20, verbose_name='帖子类型')),
                ('is_pinned', models.BooleanField(default=False, verbose_name='置顶')),
                ('is_locked', models.BooleanField(default=False, verbose_name='锁定')),
                ('view_count', models.PositiveIntegerField(default=0, verbose_name='浏览量')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('last_activity_at', models.DateTimeField(auto_now=True, verbose_name='最后活跃时间')),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='forum_topics', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'community_forum_topics',
                'ordering': ['-is_pinned', '-last_activity_at', '-id'],
            },
        ),
        migrations.CreateModel(
            name='ForumReply',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(verbose_name='回复内容')),
                ('is_best_answer', models.BooleanField(default=False, verbose_name='最佳回答')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('topic', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='community.forumtopic')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='forum_replies', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'community_forum_replies',
                'ordering': ['created_at', 'id'],
            },
        ),
    ]
