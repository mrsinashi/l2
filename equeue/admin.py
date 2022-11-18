from django.contrib import admin
from equeue.models import Cabinet, Queue

@admin.register(Cabinet)
class CabinetAdmin(admin.ModelAdmin):
    model = Cabinet
    list_display = ('cabinetnum', 'cabinetname')


@admin.register(Queue)
class QueueAdmin(admin.ModelAdmin):
    model = Queue
    list_display = ('queuename', 'queuepos', 'cabinets', 'priority')
