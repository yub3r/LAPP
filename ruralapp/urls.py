from django.urls import include, path, re_path
from ruralapp import views


urlpatterns = [
    path('ruralapp/', views.ruralapp, name='ruralapp'),
    path('ruralapp/orders-partial/', views.ruralapp_orders_partial, name='ruralapp_orders_partial'),
    path('order/', views.order_view, name='order'),
    path('misordenes/', views.mis_ordenes, name='mis_ordenes'),
    path('editar-orden/<int:order_id>/', views.edit_order, name='edit_order'),
    # path('ordenes_24hs/', views.ordenes_24hs, name='ordenes_24hs'),
    path('resumen_pedidos/', views.resumen_pedidos, name='resumen_pedidos'),  
]