from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("study", "0002_studentprofile")]
    operations = [
        migrations.CreateModel(
            name="PastPaper",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("year", models.PositiveSmallIntegerField()),
                ("exam_type", models.CharField(default="ECZ Examination", max_length=80)),
                ("file", models.FileField(upload_to="past-papers/")),
                ("is_published", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("subject", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="past_papers", to="study.subject")),
            ],
            options={"ordering": ["-year", "subject__name", "title"]},
        ),
    ]
