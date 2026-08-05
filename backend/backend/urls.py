"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('api/', include('ponds.urls')),
    path('api/', include('stocks.urls')),
    path('api/', include('growth.urls')),
    path('api/water-quality/', include('water_quality.urls')),
    path('api/weather/', include('weather.urls')),
    path('api/fish-health/', include('fish_health.urls')),
    path('api/financials/', include('financials.urls')),
    path('api/market-analysis/', include('market_analysis.urls')),
    path('api/market-bridge/', include('market_bridge.urls')),
    path('api/feeding/', include('feeding.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
