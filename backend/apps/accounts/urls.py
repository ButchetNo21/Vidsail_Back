from django.urls import path

from apps.accounts import views

urlpatterns = [
    path('login', views.LoginView.as_view()),
    path('refresh', views.RefreshView.as_view()),
    path('logout', views.LogoutView.as_view()),
    path('me', views.MeView.as_view()),
    path('permissions', views.PermissionListView.as_view()),
]
