from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'app'

router = DefaultRouter()
router.register('passwords', views.PasswordViewSet)

urlpatterns = [
    path('login/', views.LoginView.as_view()),
    path('puzzle/', views.PuzzleView.as_view()),
    path('', include(router.urls)),
]
