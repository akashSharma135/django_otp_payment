from django.urls import path
from . import views

urlpatterns = [
    path("signup/", views.UserRegister.as_view()),
    path("email_verification/", views.EmailVerification.as_view()),
    path("login/", views.UserAuth.as_view()),
]