from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # 认证
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset_password'),
    # 个人信息
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    # 查看其他用户
    path('<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    # 管理员
    path('admin/list/', views.AdminUserListView.as_view(), name='admin_user_list'),
    path('admin/<int:pk>/', views.AdminUserUpdateView.as_view(), name='admin_user_update'),
]
