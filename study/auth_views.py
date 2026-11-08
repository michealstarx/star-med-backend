import re

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.db.models import Q
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect

from django.middleware.csrf import get_token

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import StudentProfile
from .auth_serializers import (
    StudentSignupSerializer,
    normalize_phone,
)

User = get_user_model()


@ensure_csrf_cookie
def csrf_cookie(request):
    return JsonResponse({
        "csrfToken": get_token(request),
    })


class StudentSignupView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = StudentSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Create a Django session immediately so registration leads straight into learning.
        login(request, user)

        return Response(
            {
                "detail": "Account created successfully. You are now signed in.",
                "user": {
                    "id": user.pk,
                    "username": user.get_username(),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
            },
            status=status.HTTP_201_CREATED,
        )


@method_decorator(csrf_protect, name="dispatch")
class StudentLoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        identifier = request.data.get("identifier", "")
        password = request.data.get("password", "")

        if not isinstance(identifier, str) or not isinstance(password, str):
            return Response(
                {"detail": "Enter valid login details."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        identifier = identifier.strip()

        if not identifier or not password:
            return Response(
                {"detail": "Enter your username, email or phone number and password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        username = identifier

        # Email sign-in
        if "@" in identifier:
            matches = User.objects.filter(email__iexact=identifier)

            if matches.count() != 1:
                return Response(
                    {"detail": "Invalid login details."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            username = matches.first().get_username()

        # Phone sign-in
        elif any(char.isdigit() for char in identifier):
            try:
                phone = normalize_phone(identifier)
            except Exception:
                phone = None

            if phone:
                matches = User.objects.filter(
                    student_profile__phone_number=phone
                )

                if matches.count() != 1:
                    return Response(
                        {"detail": "Invalid login details."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                username = matches.first().get_username()

        user = authenticate(
            request=request,
            username=username,
            password=password,
        )

        if user is None or not user.is_active:
            return Response(
                {"detail": "Invalid login details."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        login(request, user)

        return Response({
            "detail": "Login successful.",
            "user": {
                "id": user.pk,
                "username": user.get_username(),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
        })


class StudentProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        try:
            phone_number = user.student_profile.phone_number
        except StudentProfile.DoesNotExist:
            phone_number = None

        return Response({
            "id": user.pk,
            "username": user.get_username(),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone_number": phone_number,
        })


@method_decorator(csrf_protect, name="dispatch")
class StudentLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"detail": "Logged out successfully."})

from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import PasswordResetForm
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.conf import settings
from rest_framework.throttling import AnonRateThrottle

class PasswordResetThrottle(AnonRateThrottle):
    rate = "5/hour"

class PasswordResetRequestView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetThrottle]

    def post(self, request):
        email = str(request.data.get("email", "")).strip()
        if not email:
            return Response({"detail": "Enter your account email address."}, status=400)
        form = PasswordResetForm({"email": email})
        if form.is_valid():
            # Do not reveal whether an account exists for the submitted email.
            form.save(
                request=request,
                use_https=request.is_secure(),
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                email_template_name="registration/password_reset_email.html",
                subject_template_name="registration/password_reset_subject.txt",
                extra_email_context={"frontend_url": getattr(settings, "FRONTEND_URL", "http://localhost:5173")},
            )
        return Response({"detail": "If an account matches that email, reset instructions will be sent."})

class PasswordResetConfirmView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetThrottle]

    def post(self, request):
        uidb64 = str(request.data.get("uid", ""))
        token = str(request.data.get("token", ""))
        password = request.data.get("new_password") or request.data.get("password") or ""
        if not isinstance(password, str) or len(password) < 8:
            return Response({"detail": "Use a password with at least 8 characters."}, status=400)
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid, is_active=True)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        if user is None or not default_token_generator.check_token(user, token):
            return Response({"detail": "This reset link is invalid or has expired. Request a new one."}, status=400)
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        try:
            validate_password(password, user=user)
        except ValidationError as exc:
            return Response({"detail": " ".join(exc.messages)}, status=400)
        user.set_password(password)
        user.save(update_fields=["password"])
        return Response({"detail": "Your password has been reset. You can now sign in."})
