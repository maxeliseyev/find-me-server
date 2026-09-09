"""Общие перечисления. Держим в одном месте — используются в нескольких приложениях."""

from django.db import models


class Species(models.TextChoices):
    DOG = "dog", "Собака"
    CAT = "cat", "Кошка"
    BIRD = "bird", "Птица"
    OTHER = "other", "Другое"


class Size(models.TextChoices):
    SMALL = "small", "Маленькое"
    MEDIUM = "medium", "Среднее"
    LARGE = "large", "Крупное"


class Sex(models.TextChoices):
    MALE = "male", "Самец"
    FEMALE = "female", "Самка"
    UNKNOWN = "unknown", "Неизвестно"
