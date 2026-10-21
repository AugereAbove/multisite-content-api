import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Site",
            fields=[
                ("id", models.BigAutoField(
                    auto_created=True, primary_key=True, serialize=False, verbose_name="ID",
                )),
                ("name", models.CharField(max_length=120)),
                ("slug", models.SlugField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="Page",
            fields=[
                ("id", models.BigAutoField(
                    auto_created=True, primary_key=True, serialize=False, verbose_name="ID",
                )),
                ("slug", models.SlugField()),
                ("title", models.CharField(max_length=200)),
                ("body", models.TextField(blank=True)),
                ("published", models.BooleanField(default=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("site", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="pages",
                    to="content.site",
                )),
            ],
            options={"ordering": ["slug"]},
        ),
        migrations.AddConstraint(
            model_name="page",
            constraint=models.UniqueConstraint(
                fields=("site", "slug"), name="unique_page_slug_per_site",
            ),
        ),
    ]
