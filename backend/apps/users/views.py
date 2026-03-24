from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.shortcuts import get_object_or_404

from .models import User
from .serializers import (
    RegisterSerializer, UserSerializer, UserProfileUpdateSerializer,
    UserAdminSerializer, ChangePasswordSerializer, UserPublicSerializer,
    ForgotPasswordRequestSerializer, ResetPasswordSerializer
)
from apps.textbooks.models import Textbook
from apps.textbooks.serializers import TextbookListSerializer
from utils.permissions import IsAdmin


class RegisterView(generics.CreateAPIView):
    """用户注册"""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            'message': '注册成功',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """个人信息查看和修改"""
    serializer_class = UserSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return UserProfileUpdateSerializer
        return UserSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(instance).data)


class ChangePasswordView(APIView):
    """修改密码"""
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'message': '密码修改成功'})


class ForgotPasswordView(APIView):
    """忘记密码：发送重置链接到邮箱"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        email = serializer.validated_data['email']

        user = User.objects.filter(username=username, email=email, is_active=True).first()
        # 无论用户是否存在，统一返回，避免账号枚举
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?uid={uid}&token={token}"
            send_mail(
                subject='教材共享平台 - 密码重置',
                message=(
                    f"{user.username}，您好！\n\n"
                    "我们收到了您的密码重置请求。\n"
                    "请在 30 分钟内点击以下链接重置密码：\n"
                    f"{reset_url}\n\n"
                    "如果不是您本人操作，请忽略本邮件。"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

        return Response({'message': '如果账号信息匹配，重置邮件已发送，请检查邮箱'})


class ResetPasswordView(APIView):
    """通过 uid + token 重置密码"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id, is_active=True)
        except Exception:
            return Response({'error': '重置链接无效或已过期'}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({'error': '重置链接无效或已过期'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save(update_fields=['password'])
        return Response({'message': '密码重置成功，请使用新密码登录'})


class UserDetailView(generics.RetrieveAPIView):
    """查看其他用户公开信息"""
    queryset = User.objects.all()
    serializer_class = UserPublicSerializer
    permission_classes = [permissions.AllowAny]


class UserPublishedTextbookListView(generics.ListAPIView):
    """公开查看用户已发布教材列表（含已售/已租）"""
    serializer_class = TextbookListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        user_id = self.kwargs.get('pk')
        get_object_or_404(User.objects.only('id'), pk=user_id)
        return Textbook.objects.filter(
            owner_id=user_id,
            status__in=['approved', 'sold', 'rented', 'completed', 'offline']
        ).select_related('owner', 'category').order_by('-created_at')


class AdminUserListView(generics.ListAPIView):
    """管理员 - 用户列表"""
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserAdminSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['role', 'is_verified', 'is_active', 'college']
    search_fields = ['username', 'student_id', 'email', 'phone']


class AdminUserUpdateView(generics.UpdateAPIView):
    """管理员 - 修改用户信息（角色、状态等）"""
    queryset = User.objects.all()
    serializer_class = UserAdminSerializer
    permission_classes = [IsAdmin]
