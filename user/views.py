from random import randint
from rest_framework.views import APIView
from . import serializers
from .models import CustomUser, Otp
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail, BadHeaderError
from rest_framework.authtoken.models import Token
from django.conf import settings
from rest_framework import permissions
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password


def random_with_N_digits():
    range_start = 10 ** (6 - 1)
    range_end = (10 ** 6) - 1
    return randint(range_start, range_end)

class UserRegister(APIView):
    def get_serializer(self):
        return serializers.UserRegisterSerializer()

    def post(self, request):
        email = request.data.get("email")
        phone = request.data.get("phone_number")
        if email is not None:
            isemail = CustomUser.objects.filter(email=email)
            if isemail:
                data = {"message": "This email is already registered", "field": "email"}
                return Response(data, status=status.HTTP_400_BAD_REQUEST)
        if phone is not None:
            isphone = CustomUser.objects.filter(phone_number=phone)
            if isphone:
                data = {
                    "message": "This phone number is already registered",
                    "field": "phone",
                }
                return Response(data, status=status.HTTP_400_BAD_REQUEST)
        serializer = serializers.UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            if user:
                token = Token.objects.create(user=user)
                json = serializer.data
                json["token"] = token.key
                email = str(user)
                try:
                    subject = "Please Verify your Email"
                    otp = random_with_N_digits()
                    email_message = (
                        "Hi, <br><br> Please Verify your Email by below Otp: <br><br>"
                        + str(otp)
                    )
                    send_mail(
                        subject,
                        email_message,
                        getattr(settings, "EMAIL_HOST_USER"),
                        [email],
                        fail_silently=False,
                    )
                    user_check = Otp.objects.filter(email=email)
                    if user_check:
                        user_check.update(code=otp)
                    else:
                        Otp.objects.create(email=email, code=otp)

                except BadHeaderError:
                    return Response(status=status.HTTP_400_BAD_REQUEST)
                return Response(
                    {
                        "key": token.key,
                        "message": "A  email verification otp has been sent",
                    },
                    status=status.HTTP_201_CREATED,
                )
        else:
            data = {"error": True, "errors": serializer.errors}
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


class EmailVerification(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer(self):
        return serializers.OtpSerializer()

    def post(self, request):
        code = request.data.get("code")
        try:
            otp_check = Otp.objects.get(email=request.user.email)
        except Exception:
            data = {"error": True, "message": "User Otp Doesn't exists"}
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        if str(otp_check.code) == str(code):
            CustomUser.objects.filter(email=request.user.email).update(verified=True)
            data = {"error": False, "message": "Otp successfully verified"}
            return Response(data, status=status.HTTP_200_OK)
        else:
            data = {"error": True, "message": "Otp is not correct please try again"}
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

class UserAuth(APIView):
    def get_serializer(self):
        return serializers.UserLoginSerializer()

    def post(self, request):
        isemail = CustomUser.objects.filter(email=request.data.get("email"))
        if not isemail:
            data = {
                "message": "Account with this email does not exist",
                "field": "email",
            }
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)
        if not isemail[0].is_active:
            data = {
                "message": "your account is not activated",
                "field": "email",
            }
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)

        user = authenticate(
            email=request.data.get("email"), password=request.data.get("password")
        )
        if user is not None:
            try:
                token = Token.objects.get(user_id=user.id)
            except:
                token = Token.objects.create(user=user)
            return Response({"key": token.key, "message": "Login Successful"})
        else:
            data = {
                "field": "password",
                "message": "This password is incorrect, please try again",
            }

            return Response(data, status=status.HTTP_401_UNAUTHORIZED)


class ForgotPassword(APIView):           
    def post(self, request):
        email = request.data.get("email")

        if email is not None:
            isemail = CustomUser.objects.filter(email=email)

            if not isemail:
                return Response({"msg": "Email does not exists!"}, status=status.HTTP_200_OK)

            try:
                subject = "Please Verify your Email"
                otp = random_with_N_digits()
                email_message = (
                    "Hi, <br><br> Please Verify your Email by below Otp: <br><br>"
                    + str(otp)
                )
                send_mail(
                    subject,
                    email_message,
                    getattr(settings, "EMAIL_HOST_USER"),
                    [email],
                    fail_silently=False,
                )
                user_check = Otp.objects.filter(email=email)
                if user_check:
                    user_check.update(code=otp)
                else:
                    Otp.objects.create(email=email, code=otp)

                return Response(status=status.HTTP_200_OK)

            except BadHeaderError:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            
class VerifyOtp(APIView):
    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")

        try:
            otp_check = Otp.objects.get(email=email)
        except Exception:
            data = {"error": True, "message": "User Otp Doesn't exists"}
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        if str(otp_check.code) == str(code):
            is_verified = CustomUser.objects.filter(email=email).update(verified=True)

            data = {"error": False, "message": "Otp successfully verified"}
            return Response(data, status=status.HTTP_200_OK)

class NewPassword(APIView):
    def post(self, request):
        email = request.data.get("email")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if new_password != confirm_password:
            return Response({"error": "New password and confirm password must match."}, status=status.HTTP_200_OK)

        user = CustomUser.objects.get(email=email)

        user.password = make_password(new_password)

        user.save()

        return Response({"msg": "Password has been changed!"}, status=status.HTTP_200_OK)

