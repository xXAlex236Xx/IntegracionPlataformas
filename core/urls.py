from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from miapp.views import (
    inicio, registro_view, logout_view, admin_dashboard_view, borrar_usuario, # Añadido borrar_usuario
    ProductoViewSet, CategoriaViewSet, stock_por_sucursal, crear_pedido,
    contacto, convertir_moneda
)
from django.contrib.auth import views as auth_views
from miapp.forms import LoginForm

# Import para Swagger/OpenAPI
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="API Productos",
        default_version='v1',
        description="API para consulta y pedidos de productos",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

router = DefaultRouter()
router.register(r'productos', ProductoViewSet, basename='producto')
router.register(r'categorias', CategoriaViewSet, basename='categoria')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', inicio, name='inicio'),
    path('api/', include(router.urls)),
    path('sucursales/<int:id>/stock', stock_por_sucursal),
    path('pedidos', crear_pedido),
    path('contacto', contacto),
    path('moneda/convertir', convertir_moneda),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    
    path('registro/', registro_view, name='registro'),
    path('login/', auth_views.LoginView.as_view(template_name='miapp/login.html', authentication_form=LoginForm), name='login'),
    path('logout/', logout_view, name='logout'),

    path('admin_dashboard/', admin_dashboard_view, name='crud_admin'),
    path('borrar_usuario/<int:user_id>/', borrar_usuario, name='borrar_usuario'), # NUEVA URL
]