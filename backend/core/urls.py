from django.urls import path

from . import views


urlpatterns = [
    path('homepage/', views.homepage, name='homepage'),
    path('auth/signup/', views.signup, name='signup'),
    path('auth/login/', views.login, name='login'),
    path('auth/me/', views.me, name='me'),
    path('auth/logout/', views.logout, name='logout'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/mark-read/', views.mark_notifications_read, name='mark-notifications-read'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark-notification-read'),
]
