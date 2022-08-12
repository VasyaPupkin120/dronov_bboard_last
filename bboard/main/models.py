from django.db import models
from django.contrib.auth.models import AbstractUser

# импорт для модели объявлений и модели дополнительных изображений
from .utilities import get_timestamp_path

class AdvUser(AbstractUser):
    """
    Модель пользователя. Связана с моделью объявлений.
    """
    is_activated = models.BooleanField(
            default=True,
            db_index=True,
            verbose_name='Прошел активацию'
            )
    send_messages = models.BooleanField(
            default=True,
            verbose_name='Слать сообщения об новых комментариях'
            )

    def delete(self, *args, **kwargs):
        """
        Используется менеджер обратной связи для перебора связанных
        с пользователем объявлений, для удаления всех его файлов в БД
        с помощью django_cleanup.
        """
        for bb in self.bb_set.all():
            bb.delete()
        super().delete(*args, **kwargs)

    class Meta(AbstractUser.Meta):
        pass


class Rubric(models.Model):
    """
    Базовая модель рубрик. В чистом виде не используется.
    """
    name = models.CharField(
            max_length=20,
            db_index=True,
            unique=True,
            verbose_name='Название'
            )
    order = models.SmallIntegerField(
            default=0,
            db_index=True,
            verbose_name='Порядок'
            )
    super_rubric = models.ForeignKey(
            'SuperRubric',
            on_delete=models.PROTECT,
            null=True,
            blank=True,
            verbose_name='Надрубрика'
            )


class SuperRubricManager(models.Manager):
    """
    Диспетчер записей модели надрубрик.
    """
    def get_queryset(self):
        return super().get_queryset().filter(super_rubric__isnull=True)

class SuperRubric(Rubric):
    """
    Модель надрубрик.
    """
    objects = SuperRubricManager()

    def __str__(self):
        return self.name

    class Meta:
        proxy = True
        ordering = ('order', 'name')
        verbose_name = 'Надрубрика'
        verbose_name_plural = 'Надрубрики'


class SubRubricManager(models.Manager):
    """
    Диспетчер записей подрубрик.
    """
    def get_queryset(self):
        return super().get_queryset().filter(super_rubric__isnull=False)


class SubRubric(Rubric):
    """
    Модель подрубрик.
    """
    objects = SubRubricManager()

    def __str__(self):
        return '%s - %s' % (self.super_rubric.name, self.name)

    class Meta:
        proxy = True
        ordering = ('super_rubric__order', 'super_rubric__name', 'order', 'name')
        verbose_name = 'Подрубрика'
        verbose_name_plural = 'Подрубрики'


class Bb(models.Model):
    """
    Модель объявлений. Связана с двумя первичными моделями -
    SubRubric и Advuser.
    """
    rubric = models.ForeignKey(
            SubRubric,
            on_delete = models.PROTECT,
            verbose_name = 'Рубрика'
            )
    title = models.CharField(
            max_length = 40,
            verbose_name = 'Товар'
            )
    content = models.TextField(
            verbose_name = 'Описание'
            )
    price = models.FloatField(
            default = 0,
            verbose_name = 'Цена'
            )
    contacts = models.TextField(
            verbose_name = 'Контакты'
            )
    image = models.ImageField(
            blank = True,
            upload_to = get_timestamp_path,
            verbose_name = 'Изображение'
            )
    author = models.ForeignKey(
            AdvUser,
            on_delete = models.CASCADE,
            verbose_name = 'Автор объявления'
            )
    is_active = models.BooleanField(
            default = True,
            db_index = True,
            verbose_name = 'Выводить в списке'
            )
    created_at = models.DateTimeField(
            auto_now_add = True,
            db_index = True,
            verbose_name = 'Опубликовано'
            )

    def delete(self, *args, **kwargs):
        """
        Переопределенный метод для удаления всех связанных с объявлениями 
        дополнительных иллюстраций. Используется менеджер обратной связи.
        При удалении возникает сигнал post_delete, который перехватывается
        утилитой django_cleanup, которая и удаляет все файлы в БД.
        """
        for ai in self.additionalimage_set.all():
            ai.delete()
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name_plural = 'Объявления'
        verbose_name = 'Объявление'
        ordering = ['-created_at']


class AdditionalImage(models.Model):
    """
    Модель дополнительных изображений.
    """
    bb = models.ForeignKey(
            Bb,
            on_delete = models.CASCADE,
            verbose_name = 'Объявление'
            )
    image = models.ImageField(
            upload_to = get_timestamp_path,
            verbose_name = 'Изображение'
            )

    class Meta:
        verbose_name_plural = 'Дополнительные иллюстрации'
        verbose_name = 'Дополнительная иллюстрация'


class Comment(models.Model):
    """
    Модель комментария. Связана с моделью объявлений.
    """
    bb = models.ForeignKey(
            Bb, 
            on_delete=models.CASCADE,
            verbose_name='Объявление'
            )
    author = models.CharField(
            max_length=30,
            verbose_name='Автор'
            )
    content = models.TextField(
            verbose_name='Содержание'
            )
    is_active = models.BooleanField(
            default=True,
            db_index=True,
            verbose_name='Выводить не экран?'
            )
    created_at = models.DateTimeField(
            auto_now_add=True,
            db_index=True,
            verbose_name='Опубликован'
            )

    class Meta:
        verbose_name_plural = 'Комментарии'
        verbose_name = 'Комментарий'
        ordering = ['created_at',]
