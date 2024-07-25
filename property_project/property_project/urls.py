from django.contrib import admin
from django.urls import path
from property_app.views import property_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', property_view, name='property_view'),
]
