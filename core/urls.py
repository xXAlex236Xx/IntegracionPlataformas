from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from miapp.views import (
    inicio, registro_view, login_view, logout_view, admin_dashboard_view, borrar_usuario,
    ProductoViewSet, CategoriaViewSet, stock_por_sucursal, crear_pedido,
    contacto, convertir_moneda,
    producto_list, producto_detail, producto_create, producto_update, producto_delete,
    categoria_list, categoria_create, categoria_update, categoria_delete,
    add_to_cart, remove_from_cart, update_cart_item_quantity, view_cart,
)
from django.contrib.auth import views as auth_views
from miapp.forms import LoginForm

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from django.conf import settings
from django.conf.urls.static import static

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
    path('contacto', contacto, name='contacto'),
    path('moneda/convertir', convertir_moneda),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),

    path('registro/', registro_view, name='registro'),
    path('login/', auth_views.LoginView.as_view(template_name='miapp/login.html', authentication_form=LoginForm), name='login'),
    path('logout/', logout_view, name='logout'),

    path('admin_dashboard/', admin_dashboard_view, name='crud_admin'),
    path('borrar_usuario/<int:user_id>/', borrar_usuario, name='borrar_usuario'),

    path('productos_crud/', producto_list, name='producto_list'),
    path('productos_crud/crear/', producto_create, name='producto_create'),
    path('productos_crud/<str:codigo>/', producto_detail, name='producto_detail'),
    path('productos_crud/<str:codigo>/editar/', producto_update, name='producto_update'),
    path('productos_crud/<str:codigo>/eliminar/', producto_delete, name='producto_delete'),

    path('categorias_crud/', categoria_list, name='categoria_list'),
    path('categorias_crud/crear/', categoria_create, name='categoria_create'),
    path('categorias_crud/<int:pk>/editar/', categoria_update, name='categoria_update'),
    path('categorias_crud/<int:pk>/eliminar/', categoria_delete, name='categoria_delete'),

    path('cart/', view_cart, name='view_cart'),
    path('cart/add/', add_to_cart, name='add_to_cart'),
    path('cart/remove/', remove_from_cart, name='remove_from_cart'),
    path('cart/update/', update_cart_item_quantity, name='update_cart_item_quantity'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)