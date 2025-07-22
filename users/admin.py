from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Usuario, Rol

@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    model = Usuario
    list_display = ('id', 'correo', 'nombre', 'apellido', 'rol', 'is_active', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'rol')
    search_fields = ('correo', 'nombre', 'apellido')
    ordering = ('id',)
    filter_horizontal = ()
    fieldsets = (
        (None, {'fields': ('correo', 'password')}),
        ('Información personal', {'fields': ('nombre', 'apellido', 'rol')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas importantes', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('correo', 'nombre', 'apellido', 'rol', 'password1', 'password2', 'is_staff', 'is_active')}
         ),
    )

    def save_model(self, request, obj, form, change):

        if obj.rol and obj.rol.nombre.lower() == 'administrador':
            obj.is_staff = True
        else:
            obj.is_staff = False
        super().save_model(request, obj, form, change)

@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)
