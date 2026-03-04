from django.urls import path
from . import views

urlpatterns = [
    path('conversations/', views.ConversationListView.as_view(), name='conversation_list'),
    path('conversations/create/', views.ConversationCreateView.as_view(), name='conversation_create'),
    path('conversations/<int:conversation_id>/messages/', views.MessageListView.as_view(), name='message_list'),
    path('conversations/<int:conversation_id>/send/', views.SendMessageView.as_view(), name='send_message'),
    path('unread/', views.UnreadCountView.as_view(), name='unread_count'),
]
