from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("study", "0006_external_resource_links"),
    ]

    operations = [
        migrations.AddField(
            model_name="topic",
            name="video_url",
            field=models.URLField(
                "Topic video link",
                blank=True,
                help_text="Paste a YouTube, Vimeo, Google Drive video, or direct video link. For Google Drive, allow Anyone with the link to view.",
                max_length=1000,
            ),
        ),
    ]
