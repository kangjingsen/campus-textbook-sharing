from django.urls import path
from . import views

urlpatterns = [
    path('announcements/', views.AnnouncementListView.as_view(), name='announcement_list'),
    path('announcements/manage/', views.AnnouncementManageListCreateView.as_view(), name='announcement_manage_list_create'),
    path('announcements/manage/<int:pk>/', views.AnnouncementManageDetailView.as_view(), name='announcement_manage_detail'),

    path('forum/topics/', views.ForumTopicListCreateView.as_view(), name='forum_topic_list_create'),
    path('forum/topics/<int:pk>/', views.ForumTopicDetailView.as_view(), name='forum_topic_detail'),
    path('forum/topics/<int:topic_id>/replies/', views.ForumReplyListCreateView.as_view(), name='forum_reply_list_create'),
    path('forum/topics/<int:topic_id>/best-answer/<int:reply_id>/', views.ForumBestAnswerView.as_view(), name='forum_best_answer'),
]
