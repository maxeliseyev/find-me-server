from django.contrib import admin

from .models import Pet, PetPhoto


class PetPhotoInline(admin.TabularInline):
    model = PetPhoto
    extra = 0


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ("__str__", "species", "breed", "sex", "chip_number", "created_at")
    list_filter = ("species", "size", "sex")
    search_fields = ("name", "breed", "chip_number", "brand_number", "features")
    inlines = [PetPhotoInline]
    autocomplete_fields = ("owner",)
