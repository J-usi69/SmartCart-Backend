from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

class Rol(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre

class UsuarioManager(BaseUserManager):
    def create_user(self, correo, nombre, apellido, password=None, **extra_fields):
        if not correo:
            raise ValueError('El usuario debe tener un correo electrónico')
        correo = self.normalize_email(correo)
        usuario = self.model(correo=correo, nombre=nombre, apellido=apellido, **extra_fields)
        usuario.set_password(password)
        usuario.save()
        return usuario

    def create_superuser(self, correo, nombre, apellido, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(correo, nombre, apellido, password, **extra_fields)

class Usuario(AbstractBaseUser, PermissionsMixin):
    correo = models.EmailField(unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE, null=True, blank=True)

    objects = UsuarioManager()

    USERNAME_FIELD = 'correo'
    REQUIRED_FIELDS = ['nombre', 'apellido']

    def __str__(self):
        return self.correo
