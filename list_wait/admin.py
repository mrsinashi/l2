from django.contrib import admin
from .models import ListWait


class ResListWait(admin.ModelAdmin):
    autocomplete_fields = ('client',)
    list_display = ('client', 'exec_at', 'create_at', 'research')
    list_display_links = ('client', 'exec_at', 'create_at')

    search_fields = ('research__title',)


admin.site.register(ListWait, ResListWait)
