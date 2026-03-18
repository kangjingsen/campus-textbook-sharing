from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'password_confirm',
                  'student_id', 'college', 'major', 'phone']

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({'password_confirm': '两次密码不一致'})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'student_id', 'college', 'major',
                  'phone', 'avatar', 'role', 'is_verified', 'bio',
                  'date_joined', 'created_at']
        read_only_fields = ['id', 'role', 'is_verified', 'date_joined', 'created_at']


class UserPublicSerializer(serializers.ModelSerializer):
    """公开主页序列化器，不暴露手机号/邮箱/学号"""
    class Meta:
        model = User
        fields = ['id', 'username', 'college', 'major', 'avatar', 'role',
                  'is_verified', 'bio', 'date_joined']


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'phone', 'college', 'major', 'bio', 'avatar', 'student_id']


class UserAdminSerializer(serializers.ModelSerializer):
    """管理员用的用户序列化器，可修改角色和验证状态"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'student_id', 'college', 'major',
                  'phone', 'avatar', 'role', 'is_verified', 'is_active',
                  'bio', 'date_joined', 'created_at']
        read_only_fields = ['id', 'username', 'date_joined', 'created_at']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('原密码不正确')
        return value


class ForgotPasswordRequestSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)


class ResetPasswordSerializer(serializers.Serializer):
    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': '两次密码不一致'})
        return attrs
