from django.urls import path
from . import views

urlpatterns = [
    path('', views.RecommendationListView.as_view(), name='recommendations'),
    path('popular/', views.PopularTextbooksView.as_view(), name='popular_textbooks'),
    path('history/', views.BrowsingHistoryListView.as_view(), name='browsing_history'),
]
