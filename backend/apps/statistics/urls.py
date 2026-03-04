from django.urls import path
from . import views

urlpatterns = [
    path('overview/', views.DashboardOverviewView.as_view(), name='dashboard_overview'),
    path('circulation/', views.CirculationRateView.as_view(), name='circulation_rate'),
    path('popular/', views.PopularTextbookRankView.as_view(), name='popular_rank'),
    path('price-trend/', views.PriceTrendView.as_view(), name='price_trend'),
    path('college-demand/', views.CollegeDemandView.as_view(), name='college_demand'),
    path('transaction-types/', views.TransactionTypeDistView.as_view(), name='transaction_types'),
    path('user-activity/', views.UserActivityView.as_view(), name='user_activity'),
    path('category-distribution/', views.CategoryDistributionView.as_view(), name='category_distribution'),
]
