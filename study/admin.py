from django.contrib import admin
from .models import Course, Topic, Question, Purchase, Review, PastPaper

admin.site.site_header = "STar Med · Medicine & Surgery"
admin.site.site_title = "STar Med Admin"
admin.site.index_title = "Year 2 medical learning content"


class TopicInline(admin.TabularInline):
    model = Topic
    fields = ("title", "summary", "notes_url", "video_url", "order", "is_published")
    extra = 0


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "curriculum", "is_published")
    list_filter = ("category", "is_published")
    search_fields = ("name",)
    inlines = [TopicInline]


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order", "has_notes_link", "has_video_link", "is_published")
    list_filter = ("course", "is_published")
    search_fields = ("title", "course__name")
    fields = ("course", "title", "summary", "notes_url", "video_url", "order", "is_published")

    @admin.display(boolean=True, description="PDF notes link")
    def has_notes_link(self, obj):
        return bool(obj.notes_url)

    @admin.display(boolean=True, description="Video link")
    def has_video_link(self, obj):
        return bool(obj.video_url)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("prompt", "topic", "correct_option", "is_published")
    list_filter = ("topic__course", "is_published")


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "course",
        "amount",
        "operator",
        "status",
        "created_at",
    )
    list_filter = ("status", "operator")
    search_fields = ("reference", "phone", "lenco_reference")
    readonly_fields = ("provider_payload", "created_at", "updated_at")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("student_name", "review_type", "course", "rating", "is_approved", "created_at")
    list_filter = ("review_type", "course", "is_approved", "rating")
    actions = ["approve_reviews"]

    @admin.action(description="Approve selected reviews for public display")
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)


@admin.register(PastPaper)
class PastPaperAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "year", "exam_type", "has_resource_link", "is_published")
    list_filter = ("course", "year", "exam_type", "is_published")
    search_fields = ("title", "course__name")
    fields = ("course", "title", "year", "exam_type", "external_url", "is_published", "created_at")
    readonly_fields = ("created_at",)

    @admin.display(boolean=True, description="Resource link")
    def has_resource_link(self, obj):
        return bool(obj.external_url or obj.file)
