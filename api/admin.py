from ajax_select.admin import AjaxSelectAdmin
from django.contrib import admin

import api.models as models


@admin.register(models.Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'key', 'active')


admin.site.register(models.RelationFractionASTM)

admin.site.register(models.RelationCultureASTM)


@admin.register(models.Analyzer)
class AnalyzerAdmin(AjaxSelectAdmin):
    list_display = ('__str__', 'protocol', 'mode', 'connection_string')
