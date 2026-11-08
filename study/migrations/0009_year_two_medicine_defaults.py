from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("study", "0008_rename_subject_to_course")]

    operations = [
        migrations.AlterField(
            model_name="course",
            name="curriculum",
            field=models.CharField(default="MBChB · Medicine & Surgery · Year 2", max_length=80),
        ),
        migrations.AlterField(
            model_name="course",
            name="category",
            field=models.CharField(default="Medicine", max_length=40),
        ),
        migrations.AlterField(
            model_name="pastpaper",
            name="exam_type",
            field=models.CharField(default="Medicine & Surgery Examination", max_length=80),
        ),
    ]
