from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField("создано", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("обновлено", auto_now=True)

    class Meta:
        abstract = True
