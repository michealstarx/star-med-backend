from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("study", "0003_pastpaper"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="review",
            name="user",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                related_name="academy_reviews", to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="review",
            name="subject",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                related_name="student_reviews", to="study.subject",
            ),
        ),
        migrations.AddField(
            model_name="review",
            name="review_type",
            field=models.CharField(
                choices=[("experience", "Overall experience"), ("subject", "Subject rating")],
                default="experience", max_length=12,
            ),
        ),
        migrations.AlterField(
            model_name="review",
            name="comment",
            field=models.TextField(blank=True, max_length=1000),
        ),
        migrations.AddConstraint(
            model_name="review",
            constraint=models.UniqueConstraint(
                condition=models.Q(("review_type", "experience"), ("user__isnull", False)),
                fields=("user",), name="one_experience_review_per_student",
            ),
        ),
        migrations.AddConstraint(
            model_name="review",
            constraint=models.UniqueConstraint(
                condition=models.Q(("review_type", "subject"), ("user__isnull", False)),
                fields=("user", "subject"), name="one_subject_review_per_student",
            ),
        ),
    ]
