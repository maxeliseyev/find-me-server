from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models

from apps.core.enums import Sex, Size, Species
from apps.core.models import TimeStampedModel


class Pet(TimeStampedModel):
    """Животное. Отделено от объявления: одно животное может теряться дважды."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="владелец",
        on_delete=models.CASCADE,
        related_name="pets",
    )
    name = models.CharField("кличка", max_length=64, blank=True)
    species = models.CharField("вид", max_length=16, choices=Species)
    breed = models.CharField("порода", max_length=128, blank=True)
    colors = ArrayField(models.CharField(max_length=32), verbose_name="окрас", default=list)
    size = models.CharField("размер", max_length=16, choices=Size, blank=True)
    sex = models.CharField("пол", max_length=16, choices=Sex, default=Sex.UNKNOWN)
    features = models.TextField("приметы", blank=True)

    # Раздел 4: поле чипа со ссылкой на проверку в сторонней базе.
    chip_number = models.CharField("номер чипа", max_length=32, blank=True, db_index=True)
    brand_number = models.CharField("клеймо", max_length=32, blank=True)

    class Meta:
        verbose_name = "животное"
        verbose_name_plural = "животные"

    def __str__(self):
        return f"{self.name or self.get_species_display()} ({self.owner})"


class PetPhoto(TimeStampedModel):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField("фото", upload_to="pets/%Y/%m/")
    is_primary = models.BooleanField("основное", default=False)

    class Meta:
        verbose_name = "фото животного"
        verbose_name_plural = "фото животных"
        ordering = ("-is_primary", "created_at")
