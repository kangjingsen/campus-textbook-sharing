from django.urls import path
from . import views

urlpatterns = [
    path('user-insights/', views.UserInsightsView.as_view(), name='user_insights'),
    path('overview/', views.DashboardOverviewView.as_view(), name='dashboard_overview'),
    path('circulation/', views.CirculationRateView.as_view(), name='circulation_rate'),
    path('popular/', views.PopularTextbookRankView.as_view(), name='popular_rank'),
    path('sales-ranking/', views.SalesRankingView.as_view(), name='sales_ranking'),
    path('demand-ranking/', views.DemandRankingView.as_view(), name='demand_ranking'),
    path('top-sellers/', views.TopSellersView.as_view(), name='top_sellers'),
    path('price-trend/', views.PriceTrendView.as_view(), name='price_trend'),
    path('price-metrics/', views.PriceMetricsView.as_view(), name='price_metrics'),
    path('college-demand/', views.CollegeDemandView.as_view(), name='college_demand'),
    path('transaction-types/', views.TransactionTypeDistView.as_view(), name='transaction_types'),
    path('user-activity/', views.UserActivityView.as_view(), name='user_activity'),
    path('category-distribution/', views.CategoryDistributionView.as_view(), name='category_distribution'),
    path('wishlist-demand/', views.WishlistDemandView.as_view(), name='wishlist_demand'),
    path('cancellation-insights/', views.CancellationInsightsView.as_view(), name='cancellation_insights'),
]
