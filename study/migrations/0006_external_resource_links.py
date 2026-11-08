from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("study", "0005_free_subject_access_default"),
    ]

    operations = [
        migrations.AddField(
            model_name="topic",
            name="notes_url",
            field=models.URLField(
                "PDF notes link",
                blank=True,
                help_text="Paste the Google Drive sharing link to this topic's PDF notes. Set Drive access to Anyone with the link (Viewer).",
                max_length=1000,
            ),
        ),
        migrations.AddField(
            model_name="pastpaper",
            name="external_url",
            field=models.URLField(
                "Past paper link",
                blank=True,
                help_text="Paste the Google Drive sharing link to this past paper. Set Drive access to Anyone with the link (Viewer).",
                max_length=1000,
            ),
        ),
        migrations.AlterField(
            model_name="pastpaper",
            name="file",
            field=models.FileField(blank=True, upload_to="past-papers/"),
        ),
    ]
