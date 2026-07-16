# Generated 2026-07-16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deeplFrontend', '0004_add_is_document_translation_and_download_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='documenttranslationjob',
            name='has_footnotes',
            field=models.BooleanField(
                default=False,
                verbose_name='Has footnotes or endnotes',
                help_text=(
                    'True when the translated Word document contained footnotes or '
                    'endnotes.  Always False for PowerPoint jobs.'
                ),
            ),
        ),
    ]
