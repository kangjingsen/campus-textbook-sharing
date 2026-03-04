from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.OrderCreateView.as_view(), name='order_create'),
    path('', views.OrderListView.as_view(), name='order_list'),
    path('<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('<int:pk>/confirm/', views.OrderConfirmView.as_view(), name='order_confirm'),
    path('<int:pk>/complete/', views.OrderCompleteView.as_view(), name='order_complete'),
    path('<int:pk>/cancel/', views.OrderCancelView.as_view(), name='order_cancel'),
    path('<int:pk>/return/', views.OrderReturnView.as_view(), name='order_return'),
]
