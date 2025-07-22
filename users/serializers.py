from rest_framework import serializers
from .models import Rol, Usuario

class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = '__all__'

class UsuarioSerializer(serializers.ModelSerializer):
    rol_id = serializers.PrimaryKeyRelatedField(
        queryset=Rol.objects.all(),
        source='rol',
        required=False
    )

    class Meta:
        model = Usuario
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        groups = validated_data.pop('groups', [])
        user_permissions = validated_data.pop('user_permissions', [])

        password = validated_data.pop('password')
        usuario = Usuario(**validated_data)
        usuario.set_password(password)
        usuario.save()

        if groups:
            usuario.groups.set(groups)
        if user_permissions:
            usuario.user_permissions.set(user_permissions)

        return usuario

    def update(self, instance, validated_data):
        groups = validated_data.pop('groups', [])
        user_permissions = validated_data.pop('user_permissions', [])

        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()

        if groups:
            instance.groups.set(groups)
        if user_permissions:
            instance.user_permissions.set(user_permissions)

        return instance