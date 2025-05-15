from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.contenttypes.models import ContentType
from .models import CustomGroup, CustomUser

User = get_user_model()

class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = ['id', 'app_label', 'model']

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename']

class GroupReadSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, source='group.permissions')
    group_id = serializers.IntegerField(source='group.id', read_only=True)
    name = serializers.CharField(source='group.name')

    class Meta:
        model = CustomGroup
        fields = ['group_id', 'name', 'permissions', 'is_active']

class GroupWriteSerializer(serializers.ModelSerializer):
    name = serializers.CharField(write_only=True)
    permissions = serializers.PrimaryKeyRelatedField(queryset=Permission.objects.all(), many=True, source='group.permissions')

    class Meta:
        model = CustomGroup
        fields = ['name', 'permissions', 'is_active']

    def create(self, validated_data):
        permissions = validated_data.pop('group')['permissions']
        group_name = validated_data['name']
        
        if Group.objects.filter(name=group_name).exists():
            raise serializers.ValidationError({'name': 'Já existe um grupo com este nome.'})
        
        group = Group.objects.create(name=group_name)
        custom_group = CustomGroup.objects.create(group=group, is_active=True)
        group.permissions.set(permissions)

        # Certifique-se de que o grupo de administradores tenha todas as permissões
        if group_name.lower() == 'admin':
            all_permissions = Permission.objects.all()
            group.permissions.set(all_permissions)

        return custom_group

    def update(self, instance, validated_data):
        permissions = validated_data.pop('group')['permissions']
        instance.group.name = validated_data.get('name', instance.group.name)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.group.permissions.set(permissions)
        instance.group.save()
        instance.save()
        return instance

class UserSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()
    groups = GroupReadSerializer(many=True)

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'username',
            'email', 
            'is_active', 
            'is_staff',
            'is_superuser', 
            'permissions', 
            'groups'
        ]

    def get_permissions(self, obj):
        custom_user_content_type = ContentType.objects.get(model='customuser')
        return PermissionSerializer(
            obj.user_permissions.filter(content_type=custom_user_content_type).exclude(codename__in=[
                'add_customuser', 'change_customuser', 'delete_customuser', 'view_customuser'
            ]), 
            many=True
        ).data

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email not found.")
        return value

class PasswordResetConfirmSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError("Passwords do not match.")
        return data

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['username'] = user.username
        return token

class TokenVerifySerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate(self, attrs):
        token = attrs.get('token')

        try:
            UntypedToken(token)
        except (InvalidToken, TokenError) as e:
            raise serializers.ValidationError(str(e))

        return attrs

class UserGroupSerializer(serializers.ModelSerializer):
    group_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True
    )

    class Meta:
        model = User
        fields = ['group_ids']




