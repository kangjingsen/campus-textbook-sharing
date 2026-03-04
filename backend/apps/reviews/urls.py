from django.urls import path
from . import views

urlpatterns = [
    path('pending/', views.PendingReviewListView.as_view(), name='pending_reviews'),
    path('action/<int:pk>/', views.ReviewActionView.as_view(), name='review_action'),
    path('records/', views.ReviewRecordListView.as_view(), name='review_records'),
    path('sensitive-words/', views.SensitiveWordListView.as_view(), name='sensitive_words'),
    path('sensitive-words/<int:pk>/', views.SensitiveWordDetailView.as_view(), name='sensitive_word_detail'),
]
