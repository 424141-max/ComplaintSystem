from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='complaints/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('complaints/new/', views.complaint_create, name='complaint_create'),
    path('complaints/<uuid:reference>/', views.complaint_detail, name='complaint_detail'),
    path('complaints/<uuid:reference>/review/', views.complaint_update, name='complaint_update'),
    path('complaints/<uuid:reference>/start/', views.start_work, name='start_work'),
    path('complaints/<uuid:reference>/proof/', views.upload_completion_proof, name='upload_completion_proof'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]