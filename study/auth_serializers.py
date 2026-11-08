import re

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from .models import StudentProfile

User = get_user_model()


def normalize_phone(value):
    digits = re.sub(r"\D", "", value or "")

    if digits.startswith("00"):
        digits = digits[2:]

    if digits.startswith("0") and len(digits) == 10:
        digits = "260" + digits[1:]

    # Accept Zambian mobile numbers in international digits format.
    if len(digits) != 12 or not digits.startswith("260"):
        raise serializers.ValidationError(
            "Enter a valid Zambian phone number, e.g. 0971234567."
        )

    return digits


class StudentSignupSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=25)
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        min_length=8,
        style={"input_type": "password"},
    )

    def validate_username(self, value):
        value = value.strip()

        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                "This username is already taken."
            )

        return value

    def validate_email(self, value):
        value = value.strip().lower()

        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )

        return value

    def validate_phone_number(self, value):
        phone = normalize_phone(value)

        if StudentProfile.objects.filter(phone_number=phone).exists():
            raise serializers.ValidationError(
                "An account with this phone number already exists."
            )

        return phone

    def validate_password(self, value):
        from django.contrib.auth.password_validation import validate_password

        # Validate against Django's configured password validators.
        validate_password(value)
        return value

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password")
        phone_number = validated_data.pop("phone_number")

        user = User.objects.create_user(
            password=password,
            **validated_data,
        )

        StudentProfile.objects.create(
            user=user,
            phone_number=phone_number,
        )

        return user