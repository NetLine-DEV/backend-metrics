from django.contrib.auth import authenticate, get_user_model
from rest_framework.views import APIView
from rest_framework import generics, status, permissions, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import LogoutSerializer, UserSerializer, RegisterSerializer, LoginSerializer, PasswordResetSerializer, PasswordResetConfirmSerializer, PermissionSerializer, Permission, UserGroupSerializer, GroupReadSerializer, GroupWriteSerializer
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.settings import api_settings
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from rest_framework.decorators import action
from .models import CustomGroup
from .permissions import IsAdminOrInAdminGroup

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

class LoginView(generics.CreateAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    authentication_classes = [JWTAuthentication]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user = authenticate(email=email, password=password)

        if user:
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            access_token.set_exp(lifetime=api_settings.ACCESS_TOKEN_LIFETIME)
            return Response({
                'refresh': str(refresh),
                'access': str(access_token),
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class PasswordResetView(generics.GenericAPIView):
    serializer_class = PasswordResetSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        user = User.objects.filter(email=email).first()
        if user:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            frontend_url = f'https://dashlinemt.netlify.app/reset-password/{uid}/{token}/'
            send_mail(
                'Redefinição de senha',
                f'Use este link para redefinir a sua senha:\n{frontend_url}',
                'gustavoaraujohab@gmail.com',
                [email],
                fail_silently=False,
            )
            return Response({'message': 'Password reset email sent'}, status=status.HTTP_200_OK)

        return Response({'error': 'Invalid email'}, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, token):
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user.set_password(serializer.validated_data['password'])
            user.save()
            return Response({'message': 'Password has been reset'}, status=status.HTTP_200_OK)

        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    request=LogoutSerializer,
    responses={
        205: {
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
            },
        },
        400: {
            'type': 'object',
            'properties': {
                'error': {'type': 'string'},
            },
        },
    },
)
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            refresh_token = serializer.validated_data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({'message': 'Logout successful'}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({'error': 'Invalid refresh token'}, status=status.HTTP_400_BAD_REQUEST)

@extend_schema_view(
    get=extend_schema(
        summary="Get user details",
        description="Retrieve the details of the authenticated user",
        responses={
            200: UserSerializer,
            401: {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string'},
                    'code': {'type': 'string'},
                },
            },
        },
    )
)
class UserDetailsView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, *args, **kwargs):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrInAdminGroup]

    @action(detail=True, methods=['post'], url_path='deactivate')
    def deactivate(self, request, pk=None):
        try:
            user = self.get_object()
            user.is_active = False
            user.save()
            return Response({'status': 'user deactivated'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'user not found'}, status=status.HTTP_404_NOT_FOUND)

class GroupViewSet(viewsets.ModelViewSet):
    queryset = CustomGroup.objects.all()
    permission_classes = [IsAdminOrInAdminGroup]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return GroupReadSerializer
        return GroupWriteSerializer
    @action(detail=True, methods=['post'], url_path='deactivate')
    def deactivate(self, reques, pk=None):
        try:
            group = self.get_object()
            group.is_active = False
            group.save()
            return Response({'status': 'group deactivated'}, status=status.HTTP_200_OK)
        except CustomGroup.DoesNotExist:
            return Response({'error': 'group not found'}, status=status.HTTP_404_NOT_FOUND)

class PermissionViewSet(viewsets.ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAdminOrInAdminGroup]

    def get_queryset(self):
        custom_user_content_type = ContentType.objects.get(model='customuser')
        return Permission.objects.filter(content_type=custom_user_content_type).exclude(codename__in=[
            'add_customuser', 'change_customuser', 'delete_customuser', 'view_customuser'
        ])

class AddUserToGroupView(generics.UpdateAPIView):
    queryset = User.objects.all()
    permission_classes = [IsAdminOrInAdminGroup]
    serializer_class = UserGroupSerializer

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        group_ids = request.data.get('group_ids', [])

        if not group_ids:
            user.groups.clear()
            return Response({'status': 'all groups removed from user'}, status=status.HTTP_200_OK)

        try:
            groups = Group.objects.filter(id__in=group_ids)
            if len(groups) != len(group_ids):
                return Response({'error': 'one or more groups do not exist'}, status=status.HTTP_400_BAD_REQUEST)
            
            group_ids = groups.values_list('id', flat=True)
            user.groups.set(group_ids)
            return Response({'status': 'user groups updated'}, status=status.HTTP_200_OK)
        except Group.DoesNotExist:
            return Response({'error': 'one or more groups do not exist'}, status=status.HTTP_400_BAD_REQUEST)

