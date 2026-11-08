from django.db import migrations, models


def set_existing_subjects_free(apps, schema_editor):
    Subject = apps.get_model("study", "Subject")
    Subject.objects.all().update(price_zmw=0)


def restore_default_prices(apps, schema_editor):
    Subject = apps.get_model("study", "Subject")
    Subject.objects.all().update(price_zmw=50)


class Migration(migrations.Migration):
    dependencies = [("study", "0004_student_review_ratings")]

    operations = [
        migrations.AlterField(
            model_name="subject",
            name="price_zmw",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=8),
        ),
        migrations.RunPython(set_existing_subjects_free, restore_default_prices),
    ]
