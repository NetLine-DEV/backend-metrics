from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LogoutView, RegisterView, LoginView, PasswordResetView, UserDetailsView, PasswordResetConfirmView, GroupViewSet, UserViewSet, PermissionViewSet, AddUserToGroupView

router = DefaultRouter()
router.register(r'groups', GroupViewSet)
router.register(r'users', UserViewSet)
router.register(r'permissions', PermissionViewSet)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('user-details/', UserDetailsView.as_view(), name='user_details'),
    path('password_reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password_reset_confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('users/<int:pk>/add-to-group/', AddUserToGroupView.as_view(), name='add-user-to-group'),
    path('', include(router.urls)),
]