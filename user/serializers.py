from rest_framework import serializers
from .models import CustomUser
from django.contrib.auth.hashers import make_password

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:

        model = CustomUser
        fields = ("email","password","name", "phone_number")

    def create(self, validated_data):
        email = validated_data.pop("email", None)
        password = validated_data.pop("password", None)
        user = CustomUser.objects.create(
            email=email, password=make_password(password), **validated_data
        )
        return user
        # is called if we save serializer if it have an instance

    def update(self, instance, validated_data):
        instance.__dict__.update(validated_data)
        instance.save()
        return instance