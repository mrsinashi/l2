from django.db import models


class Cabinet(models.Model):
    cabinetnum = models.IntegerField(db_index=True, help_text='Номер кабинета')
    cabinetname = models.CharField(max_length=48, db_index=True, help_text='Название кабинета')

    class Meta:
        verbose_name = 'Кабинет'
        verbose_name_plural = 'Кабинеты'

    def __str__(self):
        return f"Кабинет №{self.cabinetnum}: {self.cabinetname}"

class Queue(models.Model):
    queuename = models.CharField(default='Новая Очередь', max_length=48, db_index=True, help_text='Название очереди')
    queuepos = models.IntegerField(null=True, blank=True, db_index=True, help_text='Номер очереди')
    cabinetsid = models.ManyToManyField(Cabinet, help_text="Кабинет")
    priority = models.IntegerField(default='0', db_index=True, help_text='Приоритет в очереди')

    def cabinets(self):
        return "; ".join([str(f"[{c}]") for c in self.cabinetsid.all()])

    def __str__(self):
        return f"Очередь: {self.queuename}, позиция {self.queuepos}"

    class Meta:
        verbose_name = 'Очередь'
        verbose_name_plural = 'Очереди'
