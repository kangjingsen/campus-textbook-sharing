from rest_framework import serializers
from .models import Category, Textbook, TextbookVote, TextbookComment, SharedResource, ResourceOrder


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'level', 'sort_order', 'is_active', 'children']

    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        return CategorySerializer(children, many=True).data


class CategoryFlatSerializer(serializers.ModelSerializer):
    """扁平化分类序列化器（用于下拉选择）"""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'level', 'full_name']

    def get_full_name(self, obj):
        names = [obj.name]
        parent = obj.parent
        while parent:
            names.insert(0, parent.name)
            parent = parent.parent
        return ' > '.join(names)


class TextbookListSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    owner_college = serializers.CharField(source='owner.college', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, default='')
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    condition_display = serializers.CharField(source='get_condition_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    likes_count = serializers.SerializerMethodField()
    dislikes_count = serializers.SerializerMethodField()

    class Meta:
        model = Textbook
        fields = ['id', 'title', 'author', 'isbn', 'publisher', 'price',
                  'transaction_type', 'transaction_type_display',
                  'condition', 'condition_display',
                  'status', 'status_display',
                  'cover_image', 'view_count',
                  'owner', 'owner_name', 'owner_college',
                  'category', 'category_name',
                  'likes_count', 'dislikes_count',
                  'created_at']

    def get_likes_count(self, obj):
        return obj.votes.filter(vote=1).count()

    def get_dislikes_count(self, obj):
        return obj.votes.filter(vote=-1).count()


class TextbookDetailSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    owner_college = serializers.CharField(source='owner.college', read_only=True)
    owner_avatar = serializers.ImageField(source='owner.avatar', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, default='')
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    condition_display = serializers.CharField(source='get_condition_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Textbook
        fields = '__all__'
        read_only_fields = ['owner', 'status', 'view_count', 'created_at', 'updated_at']


class TextbookCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Textbook
        fields = ['title', 'author', 'isbn', 'publisher', 'edition',
                  'condition', 'description', 'price', 'original_price',
                  'transaction_type', 'rent_duration', 'category', 'cover_image']

    def validate(self, attrs):
        if attrs.get('transaction_type') == 'free':
            attrs['price'] = 0
        if attrs.get('transaction_type') == 'rent' and not attrs.get('rent_duration'):
            raise serializers.ValidationError({'rent_duration': '租赁类型必须指定租赁天数'})
        return attrs

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        validated_data['status'] = 'pending_review'
        return super().create(validated_data)


class TextbookCommentSerializer(serializers.ModelSerializer):
    """评论序列化器"""
    username = serializers.CharField(source='user.username', read_only=True)
    avatar = serializers.ImageField(source='user.avatar', read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = TextbookComment
        fields = ['id', 'textbook', 'user', 'username', 'avatar', 'content', 'parent', 'replies', 'created_at']
        read_only_fields = ['user', 'textbook', 'created_at']

    def get_replies(self, obj):
        if obj.parent is None:
            replies = obj.replies.all()[:10]
            return TextbookCommentSerializer(replies, many=True).data
        return []


class SharedResourceSerializer(serializers.ModelSerializer):
    """共享资料序列化器"""
    uploader_name = serializers.CharField(source='uploader.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, default='')
    resource_type_display = serializers.CharField(source='get_resource_type_display', read_only=True)
    sale_type_display = serializers.CharField(source='get_sale_type_display', read_only=True)
    can_download = serializers.SerializerMethodField()
    my_order_id = serializers.SerializerMethodField()
    my_order_status = serializers.SerializerMethodField()
    my_payment_qr = serializers.SerializerMethodField()

    class Meta:
        model = SharedResource
        fields = ['id', 'title', 'description', 'file', 'file_size', 'resource_type',
                  'resource_type_display', 'sale_type', 'sale_type_display', 'price',
                  'category', 'category_name',
                  'uploader', 'uploader_name', 'download_count',
                  'can_download', 'my_order_id', 'my_order_status', 'my_payment_qr',
                  'created_at']
        read_only_fields = ['uploader', 'file_size', 'download_count', 'created_at']

    def _my_order(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        return ResourceOrder.objects.filter(resource=obj, buyer=request.user).order_by('-created_at').first()

    def get_can_download(self, obj):
        request = self.context.get('request')
        if obj.sale_type == 'free':
            return True
        if not request or not request.user.is_authenticated:
            return False
        if request.user.id == obj.uploader_id or request.user.role in ('admin', 'superadmin'):
            return True
        return ResourceOrder.objects.filter(resource=obj, buyer=request.user, status='completed').exists()

    def get_my_order_id(self, obj):
        order = self._my_order(obj)
        return order.id if order else None

    def get_my_order_status(self, obj):
        order = self._my_order(obj)
        return order.status if order else ''

    def get_my_payment_qr(self, obj):
        order = self._my_order(obj)
        if not order:
            return ''
        if order.payment_qr_image:
            return order.payment_qr_image.url
        return order.payment_qr

    def to_representation(self, instance):
        data = super().to_representation(instance)
        can_download = data.get('can_download', False)
        if instance.sale_type == 'sell' and not can_download:
            data['file'] = ''
        return data


class SharedResourceCreateSerializer(serializers.ModelSerializer):
    """共享资料上传序列化器"""
    class Meta:
        model = SharedResource
        fields = ['title', 'description', 'file', 'resource_type', 'sale_type', 'price', 'category']

    def validate(self, attrs):
        if attrs.get('sale_type') == 'free':
            attrs['price'] = 0
        elif attrs.get('price', 0) <= 0:
            raise serializers.ValidationError({'price': '售卖资料价格必须大于 0'})
        return attrs

    def create(self, validated_data):
        validated_data['uploader'] = self.context['request'].user
        if validated_data.get('file'):
            validated_data['file_size'] = validated_data['file'].size
        return super().create(validated_data)


class ResourceOrderSerializer(serializers.ModelSerializer):
    resource_title = serializers.CharField(source='resource.title', read_only=True)
    buyer_name = serializers.CharField(source='buyer.username', read_only=True)
    seller_name = serializers.CharField(source='seller.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ResourceOrder
        fields = [
            'id', 'resource', 'resource_title', 'buyer', 'buyer_name', 'seller', 'seller_name',
            'price', 'status', 'status_display', 'payment_qr', 'payment_qr_image', 'payment_proof', 'note',
            'created_at', 'updated_at', 'confirmed_at', 'paid_at', 'completed_at'
        ]
        read_only_fields = ['id', 'buyer', 'seller', 'price', 'created_at', 'updated_at', 'confirmed_at', 'paid_at', 'completed_at']


class ResourceOrderCreateSerializer(serializers.Serializer):
    resource_id = serializers.IntegerField()
    note = serializers.CharField(required=False, default='', allow_blank=True)
