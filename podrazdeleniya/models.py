from django.db import models


class Podrazdeleniya(models.Model):  # Модель подразделений
    title = models.CharField(max_length=255)  # Название подразделения
    gid_n = models.IntegerField(default=None, null=True, blank=True)  # gidNumber в LDAP
    isLab = models.BooleanField(default=False, blank=True)  # True=Это лаборатория
    hide = models.BooleanField(default=False, blank=True)  # True=Скрывать подразделение
    def __str__(self):  # Функция перевода экземпляра класса Podrazdeleniya в строку
        return self.title  # Возврат поля Podrazdeleniya.title


class Subgroups(models.Model):  # Модель подгрупп подразделений
    title = models.CharField(max_length=255)  # Название подгруппы
    podrazdeleniye = models.ForeignKey(Podrazdeleniya)  # Подразделение группы

    def __str__(self):
        if self.podrazdeleniye.title != self.title:
            return self.podrazdeleniye.title + " - " + self.title
        return self.title
