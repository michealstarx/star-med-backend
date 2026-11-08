import os, re, uuid, requests
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Course, Topic, Question, Purchase, Review, PastPaper
from .serializers import (
    CourseSerializer,
    TopicSerializer,
    QuestionSerializer,
    ReviewSerializer,
    PastPaperSerializer,
)
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET

FREE_ACCESS_MODE = os.getenv("ACADEMY_FREE_ACCESS", "true").lower() == "true"


class CourseList(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CourseSerializer
    queryset = Course.objects.filter(is_published=True).prefetch_related("topics")


class CourseDetail(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = CourseSerializer
    queryset = Course.objects.filter(is_published=True)


class TopicList(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = TopicSerializer

    def get_queryset(self):
        qs = Topic.objects.filter(is_published=True, course__is_published=True)
        course_id = self.request.query_params.get("course")
        return qs.filter(course_id=course_id) if course_id else qs


class QuestionList(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = QuestionSerializer

    def get_queryset(self):
        qs = Question.objects.filter(
            is_published=True,
            topic__is_published=True,
            topic__course__is_published=True,
        )
        topic_id = self.request.query_params.get("topic")
        return qs.filter(topic_id=topic_id) if topic_id else qs


class ReviewListCreate(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer

    def get_permissions(self):
        return [IsAuthenticated()] if self.request.method == "POST" else [AllowAny()]

    def get_queryset(self):
        return Review.objects.filter(is_approved=True).select_related("course").order_by("-created_at")

    def perform_create(self, serializer):
        user = self.request.user
        review_type = serializer.validated_data.get("review_type", "experience")
        course = serializer.validated_data.get("course")
        existing = Review.objects.filter(user=user, review_type=review_type)
        existing = existing.filter(course=course) if review_type == "course" else existing
        if existing.exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"detail": "You have already submitted this rating. Contact support if you need it changed."})
        full_name = " ".join(part for part in [user.first_name, user.last_name] if part).strip()
        serializer.save(
            user=user,
            student_name=full_name or user.get_username(),
            is_approved=False,
        )


class PaymentThrottle(AnonRateThrottle):
    rate = "10/hour"


@api_view(["POST"])
@throttle_classes([PaymentThrottle])
def initiate_payment(request):
    """Create a collection only when free access has intentionally been disabled."""
    if FREE_ACCESS_MODE:
        return Response({"detail": "STar Med is currently free. Payments are disabled."}, status=410)
    course_name = str(request.data.get("course_name", "")).strip()
    course_id = request.data.get("course_id")
    course = (
        get_object_or_404(Course, pk=course_id, is_published=True)
        if course_id
        else get_object_or_404(Course, name=course_name, is_published=True)
    )
    phone = re.sub(r"[\s-]", "", str(request.data.get("phone", "")))
    operator = str(request.data.get("operator", "")).lower()
    if operator not in {"mtn", "airtel", "zamtel"}:
        return Response({"detail": "Choose MTN, Airtel or Zamtel."}, status=400)
    if not re.fullmatch(r"(?:\+?260|0)?[0-9]{9}", phone):
        return Response(
            {"detail": "Enter a valid Zambian mobile-money number."}, status=400
        )
    api_key = os.getenv("LENCO_API_KEY", "").strip()
    if not api_key:
        return Response(
            {
                "detail": "Payment gateway is not configured yet. Set LENCO_API_KEY on the Django server."
            },
            status=503,
        )
    reference = f"MED2-{uuid.uuid4().hex[:24]}"
    # Persist the expected price from the database before contacting the gateway.
    purchase = Purchase.objects.create(
        course=course,
        reference=reference,
        phone=phone,
        operator=operator,
        amount=course.price_zmw,
    )
    base = os.getenv("LENCO_BASE_URL", "https://api.lenco.co/access/v2").rstrip("/")
    payload = {
        "amount": float(course.price_zmw),
        "reference": reference,
        "phone": phone,
        "operator": operator,
        "country": "zm",
        "bearer": os.getenv("LENCO_BEARER", "merchant"),
    }
    try:
        resp = requests.post(
            f"{base}/collections/mobile-money",
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=20,
        )
        data = resp.json()
    except (requests.RequestException, ValueError):
        purchase.status = "failed"
        purchase.save(update_fields=["status", "updated_at"])
        return Response(
            {"detail": "Could not contact the payment provider. Please try again."},
            status=502,
        )
    if not resp.ok or not data.get("status"):
        purchase.status = "failed"
        purchase.provider_payload = data if isinstance(data, dict) else {}
        purchase.save()
        return Response(
            {
                "detail": (
                    data.get("message", "Lenco could not start this payment.")
                    if isinstance(data, dict)
                    else "Lenco payment failed to start."
                )
            },
            status=502,
        )
    provider_data = data.get("data") or {}
    purchase.lenco_reference = str(provider_data.get("lencoReference", ""))
    purchase.lenco_id = str(provider_data.get("id", ""))
    provider_status = provider_data.get("status", "pending")
    purchase.status = (
        provider_status
        if provider_status in {"pending", "successful", "failed", "pay-offline"}
        else "pending"
    )
    purchase.provider_payload = {
        "status": provider_status,
        "message": data.get("message", ""),
    }
    purchase.save()
    return Response(
        {
            "reference": purchase.reference,
            "status": purchase.status,
            "message": data.get(
                "message", "Payment request initiated. Approve it on your phone."
            ),
            "amount": str(purchase.amount),
            "currency": "ZMW",
        },
        status=201,
    )


@api_view(["POST"])
@throttle_classes([PaymentThrottle])
def verify_payment(request):
    """Verify a collection only when free access has intentionally been disabled."""
    if FREE_ACCESS_MODE:
        return Response({"detail": "STar Med is currently free. Payment verification is disabled."}, status=410)
    reference = str(request.data.get("reference", "")).strip()
    if not reference:
        return Response({"detail": "Payment reference is required."}, status=400)
    purchase = get_object_or_404(Purchase, reference=reference)
    api_key = os.getenv("LENCO_API_KEY", "").strip()
    if not api_key:
        return Response({"detail": "Payment gateway is not configured."}, status=503)
    base = os.getenv("LENCO_BASE_URL", "https://api.lenco.co/access/v2").rstrip("/")
    try:
        resp = requests.get(
            f"{base}/collections/status/{purchase.reference}",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
            },
            timeout=20,
        )
        data = resp.json()
    except (requests.RequestException, ValueError):
        return Response(
            {"detail": "Unable to verify with Lenco right now. Please try again."},
            status=502,
        )
    if not resp.ok or not data.get("status"):
        return Response(
            {
                "detail": (
                    data.get("message", "Lenco status verification failed.")
                    if isinstance(data, dict)
                    else "Status verification failed."
                )
            },
            status=502,
        )
    provider_data = data.get("data") or {}
    provider_status = provider_data.get("status", "pending")
    if provider_status not in {"pending", "successful", "failed", "pay-offline"}:
        provider_status = "pending"
    # Check amount and currency before granting access. This starter expects ZMW.
    if provider_status == "successful":
        try:
            paid_amount = Decimal(str(provider_data.get("amount", "0")))
            currency = str(provider_data.get("currency", "ZMW")).upper()
        except Exception:
            return Response(
                {"detail": "Provider returned an invalid amount."}, status=502
            )
        if paid_amount != purchase.amount or currency not in {"ZMW", "ZMW ", "ZMK"}:
            return Response(
                {
                    "detail": "Payment amount or currency does not match the purchase. Access was not granted."
                },
                status=409,
            )
    with transaction.atomic():
        purchase.status = provider_status
        purchase.lenco_reference = str(
            provider_data.get("lencoReference") or purchase.lenco_reference
        )
        purchase.lenco_id = str(provider_data.get("id") or purchase.lenco_id)
        purchase.provider_payload = {
            "status": provider_status,
            "completedAt": provider_data.get("completedAt"),
            "reasonForFailure": provider_data.get("reasonForFailure"),
        }
        purchase.save()
    return Response(
        {
            "reference": purchase.reference,
            "status": purchase.status,
            "course": purchase.course.name,
            "access_granted": purchase.status == "successful",
        }
    )


@api_view(["GET"])
def health(request):
    return Response(
        {
            "status": "ok",
            "service": "STar Med · Medicine & Surgery Year 2 API",
            "curriculum": "MBChB · Medicine & Surgery · Year 2",
            "price_per_course_zmw": "0.00" if FREE_ACCESS_MODE else "50.00",
            "free_access": FREE_ACCESS_MODE,
        }
    )


@require_GET
@ensure_csrf_cookie
def csrf(request):
    return JsonResponse({"csrfToken": get_token(request)})


class PastPaperList(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = PastPaperSerializer
    queryset = PastPaper.objects.filter(is_published=True, course__is_published=True).select_related("course")
