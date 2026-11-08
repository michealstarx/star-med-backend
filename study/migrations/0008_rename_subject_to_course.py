from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("study", "0007_topic_video_url")]

    operations = [
        migrations.RemoveConstraint(
            model_name="review", name="one_experience_review_per_student"
        ),
        migrations.RemoveConstraint(
            model_name="review", name="one_subject_review_per_student"
        ),
        migrations.RenameModel(old_name="Subject", new_name="Course"),
        migrations.RenameField(model_name="topic", old_name="subject", new_name="course"),
        migrations.RenameField(model_name="purchase", old_name="subject", new_name="course"),
        migrations.RenameField(model_name="review", old_name="subject", new_name="course"),
        migrations.RenameField(model_name="pastpaper", old_name="subject", new_name="course"),
        migrations.AlterField(
            model_name="course", name="curriculum",
            field=models.CharField(default="University Foundation", max_length=80),
        ),
        migrations.AlterField(
            model_name="course", name="category",
            field=models.CharField(default="General", max_length=40),
        ),
        migrations.AlterField(
            model_name="pastpaper", name="exam_type",
            field=models.CharField(default="University Examination", max_length=80),
        ),
        migrations.AlterField(
            model_name="review", name="review_type",
            field=models.CharField(
                choices=[("experience", "Overall experience"), ("course", "Course rating")],
                default="experience", max_length=12,
            ),
        ),
        migrations.AddConstraint(
            model_name="review",
            constraint=models.UniqueConstraint(
                condition=models.Q(review_type="experience", user__isnull=False),
                fields=("user",), name="one_experience_review_per_student",
            ),
        ),
        migrations.AddConstraint(
            model_name="review",
            constraint=models.UniqueConstraint(
                condition=models.Q(review_type="course", user__isnull=False),
                fields=("user", "course"), name="one_course_review_per_student",
            ),
        ),
        migrations.AlterModelOptions(
            name="pastpaper", options={"ordering": ["-year", "course__name", "title"]},
        ),
    ]
