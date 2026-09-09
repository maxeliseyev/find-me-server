from django.contrib import admin

from .models import Message, Thread


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("author", "body", "created_at")


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ("id", "report", "created_at")
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "thread", "author", "is_hidden", "created_at")
    list_filter = ("is_hidden",)
    search_fields = ("body",)
