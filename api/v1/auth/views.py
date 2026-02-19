"""
Custom JWT Token Views with User Data
"""
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom serializer to include user data in token response"""
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add user data to response
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'is_staff': self.user.is_staff,
        }
        
        return data


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom login view that returns user data with tokens"""
    serializer_class = CustomTokenObtainPairSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def get_csrf_token(request):
    """
    Endpoint to get CSRF token.
    Il decorator ensure_csrf_cookie fa sì che Django invii il cookie csrftoken.
    """
    return Response({'detail': 'CSRF cookie set'})
