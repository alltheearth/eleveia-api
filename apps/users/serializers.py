
# ===================================================================
# apps/users/serializers.py
# ===================================================================
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """User profile serializer"""
    school_name = serializers.CharField(source='school.school_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id',
            'user',
            'school',
            'school_name',
            'role',
            'role_display',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """User serializer with profile"""
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_superuser',
            'is_staff',
            'profile',
        ]
        read_only_fields = ['id', 'is_superuser', 'is_staff']


class RegisterSerializer(serializers.Serializer):
    """User registration serializer"""
    username = serializers.CharField(required=True, max_length=150)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, min_length=8)
    password2 = serializers.CharField(required=True, write_only=True, min_length=8)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    
    school_id = serializers.IntegerField(required=False, allow_null=True)
    role = serializers.ChoiceField(
        choices=['manager', 'operator'],
        required=False,
        allow_null=True
    )
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value
    
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords don't match"})
        
        request = self.context.get('request')
        is_superuser = (
            request and request.user and 
            request.user.is_authenticated and
            (request.user.is_superuser or request.user.is_staff)
        )
        
        if not is_superuser:
            if not data.get('school_id'):
                raise serializers.ValidationError({
                    "school_id": "School is required"
                })
            if not data.get('role'):
                raise serializers.ValidationError({
                    "role": "Role is required (manager or operator)"
                })
        
        return data
    
    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        school_id = validated_data.pop('school_id', None)
        role = validated_data.pop('role', None)
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=password,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        
        if school_id and role:
            UserProfile.objects.create(
                user=user,
                school_id=school_id,
                role=role
            )
        
        return user


class LoginSerializer(serializers.Serializer):
    """Login serializer"""
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, data):
        user = authenticate(
            username=data.get('username'),
            password=data.get('password')
        )
        
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        
        data['user'] = user
        return data
