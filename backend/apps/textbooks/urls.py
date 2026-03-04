from django.urls import path
from . import views

urlpatterns = [
    # 分类
    path('categories/tree/', views.CategoryTreeView.as_view(), name='category_tree'),
    path('categories/flat/', views.CategoryFlatListView.as_view(), name='category_flat'),
    path('categories/manage/', views.CategoryManageView.as_view(), name='category_manage'),
    path('categories/manage/<int:pk>/', views.CategoryDetailManageView.as_view(), name='category_manage_detail'),
    # 教材
    path('', views.TextbookListView.as_view(), name='textbook_list'),
    path('search/', views.TextbookSearchView.as_view(), name='textbook_search'),
    path('create/', views.TextbookCreateView.as_view(), name='textbook_create'),
    path('<int:pk>/', views.TextbookDetailView.as_view(), name='textbook_detail'),
    path('<int:pk>/edit/', views.TextbookUpdateView.as_view(), name='textbook_edit'),
    path('<int:pk>/delete/', views.TextbookDeleteView.as_view(), name='textbook_delete'),
    path('my/', views.MyTextbookListView.as_view(), name='my_textbooks'),
    # 管理员删除
    path('admin/<int:pk>/delete/', views.AdminTextbookDeleteView.as_view(), name='admin_textbook_delete'),
    # 点赞/点踩
    path('<int:pk>/vote/', views.TextbookVoteView.as_view(), name='textbook_vote'),
    # 评论
    path('<int:pk>/comments/', views.TextbookCommentListView.as_view(), name='textbook_comments'),
    path('comments/<int:pk>/delete/', views.TextbookCommentDeleteView.as_view(), name='comment_delete'),
    # 在线资料共享区
    path('resources/', views.SharedResourceListView.as_view(), name='resource_list'),
    path('resources/<int:pk>/', views.SharedResourceDetailView.as_view(), name='resource_detail'),
    path('resources/<int:pk>/download/', views.SharedResourceDownloadView.as_view(), name='resource_download'),
]
