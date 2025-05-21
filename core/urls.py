"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from miapp.views import inicio

from miapp.views import (
    ProductoViewSet, CategoriaViewSet,
    stock_por_sucursal, crear_pedido,
    contacto, convertir_moneda
)

# Import para Swagger/OpenAPI
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Configuración de Swagger
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

    # Rutas API
    path('', inicio, name='inicio'),
    path('sucursales/<int:id>/stock', stock_por_sucursal),
    path('pedidos', crear_pedido),
    path('contacto', contacto),
    path('moneda/convertir', convertir_moneda),

    # Documentación Swagger/OpenAPI
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]
