import uuid
from django.conf import settings
from django.db import models



class Course(models.Model):
    curriculum = models.CharField(max_length=80, default="MBChB · Medicine & Surgery · Year 2")
    name = models.CharField(max_length=120, unique=True)
    category = models.CharField(max_length=40, default="Medicine")
    description = models.TextField(blank=True)
    price_zmw = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_published = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Topic(models.Model):
    course = models.ForeignKey(
        Course, related_name="topics", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=180)
    summary = models.TextField(blank=True)
    notes_url = models.URLField(
        "PDF notes link",
        max_length=1000,
        blank=True,
        help_text=(
            "Paste the Google Drive sharing link to this topic's PDF notes. "
            "Set Drive access to Anyone with the link (Viewer)."
        ),
    )
    video_url = models.URLField(
        "Topic video link",
        max_length=1000,
        blank=True,
        help_text=(
            "Paste a YouTube, Vimeo, Google Drive video, or direct video link. "
            "For Google Drive, allow Anyone with the link to view."
        ),
    )
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.course.name}: {self.title}"


class Question(models.Model):
    topic = models.ForeignKey(Topic, related_name="questions", on_delete=models.CASCADE)
    prompt = models.TextField()
    option_a = models.CharField(max_length=500)
    option_b = models.CharField(max_length=500)
    option_c = models.CharField(max_length=500)
    option_d = models.CharField(max_length=500)
    correct_option = models.CharField(
        max_length=1, choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")]
    )
    explanation = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)

    def __str__(self):
        return self.prompt[:70]


def generate_purchase_reference():
    return f"MED2-{uuid.uuid4().hex}"


class Purchase(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("successful", "Successful"),
        ("failed", "Failed"),
        ("pay-offline", "Awaiting approval"),
    ]
    course = models.ForeignKey(
        Course, related_name="purchases", on_delete=models.PROTECT
    )
    reference = models.CharField(
        max_length=80, unique=True, default=generate_purchase_reference
    )
    phone = models.CharField(max_length=20)
    operator = models.CharField(
        max_length=10,
        choices=[("mtn", "MTN"), ("airtel", "Airtel"), ("zamtel", "Zamtel")],
    )
    amount = models.DecimalField(max_digits=8, decimal_places=2, default=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    lenco_reference = models.CharField(max_length=100, blank=True)
    lenco_id = models.CharField(max_length=100, blank=True)
    provider_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.reference} · {self.course.name} · {self.status}"


class Review(models.Model):
    REVIEW_TYPES = [("experience", "Overall experience"), ("course", "Course rating")]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="academy_reviews", null=True, blank=True
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="student_reviews",
        null=True, blank=True
    )
    review_type = models.CharField(max_length=12, choices=REVIEW_TYPES, default="experience")
    student_name = models.CharField(max_length=80)
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField(max_length=1000, blank=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user"], condition=models.Q(review_type="experience", user__isnull=False),
                name="one_experience_review_per_student"
            ),
            models.UniqueConstraint(
                fields=["user", "course"], condition=models.Q(review_type="course", user__isnull=False),
                name="one_course_review_per_student"
            ),
        ]

    def __str__(self):
        return f"{self.rating}/5 - {self.student_name}"


class StudentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.user.get_username()

class PastPaper(models.Model):
    course = models.ForeignKey(Course, related_name="past_papers", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    year = models.PositiveSmallIntegerField()
    exam_type = models.CharField(max_length=80, default="Medicine & Surgery Examination")
    external_url = models.URLField(
        "Past paper link",
        max_length=1000,
        blank=True,
        help_text=(
            "Paste the Google Drive sharing link to this past paper. "
            "Set Drive access to Anyone with the link (Viewer)."
        ),
    )
    # Kept optional for compatibility with any papers uploaded before link-based resources.
    # It is intentionally hidden from the admin form; new resources should use external_url.
    file = models.FileField(upload_to="past-papers/", blank=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-year", "course__name", "title"]

    def __str__(self):
        return f"{self.course.name} · {self.year} · {self.title}"
