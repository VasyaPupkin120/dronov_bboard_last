import datetime

# импорты для редактора пользователей
from django.contrib import admin
from .models import AdvUser
from .utilities import send_activation_notification

# импорты для редакторов надрубрик и подрубрик
from .models import SuperRubric, SubRubric
from .forms import SubRubricForm

# импорт для редакторов объявлений и дополнительных иллюстраций
from .models import Bb, AdditionalImage

def send_activation_notifications(modeladmin, request, queryset):
    """
    Отправляет письма с требованием активации всем пользователям из списка.
    """
    for rec in queryset:
        if not rec.is_activated:
            send_activation_notification(rec)
    modeladmin.message_user(request, 'Письма с требованиями отправлены')
send_activation_notifications.short_description = 'Отправки писем с требованиями активации'


class NonactivatedFilter(admin.SimpleListFilter):
    """
    Выборка (фильтрация) пользователей по признаку активации.
    """
    title = 'Прошли активацию'
    parameter_name = 'actstate'

    def lookups(self, request, model_admin):
        return (
                ('activated', 'Прошли'),
                ('threedays', 'Не прошли более 3 дней'),
                ('week', 'Не прошли более недели'),
                )

    def queryset(self, request, queryset):
        val = self.value()
        if val == 'acitvated':
            return queryset.filter(
                    is_active=True,
                    is_activated=True
                    )
        elif val == 'threedays':
            d = datetime.date.today() - datetime.timedelta(days=3)
            return queryset.filter(
                    is_active = False,
                    is_activated = False,
                    date_joined__date__lt = d
                    )
        elif val == 'week':
            d = datetime.date.today() - datetime.timedelta(days=3)
            return queryset.filter(
                    is_active = False,
                    is_activated = False,
                    date_joined__date__lt = d
                    )


class AdvUserAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'is_activated', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = (NonactivatedFilter,)
    fields = (
            ('username', 'email'),
            ('first_name', 'last_name'),
            ('send_messages', 'is_active', 'is_activated'),
            ('is_staff', 'is_superuser'),
            'groups',
            'user_permissions',
            ('last_login', 'date_joined'),
            )
    readonly_fields = ('last_login', 'date_joined')
    actions = (send_activation_notifications,)


class SubRubricInline(admin.TabularInline):
    """
    Встроенный в SuperRubricAdmin редактор подрубрик.
    """
    model = SubRubric


class SuperRubricAdmin(admin.ModelAdmin):
    """
    Редактор надрубрик.
    """
    exclude = ('super_rubric',)
    inlines = (SubRubricInline,)


class SubRubricAdmin(admin.ModelAdmin):
    """
    Редактор подрубрик.
    """
    form = SubRubricForm


class AdditionalImageInline(admin.TabularInline):
    """
    Встроенный редактор дополнительных изображений.
    """
    model = AdditionalImage


class BbAdmin(admin.ModelAdmin):
    """
    Редактор объявлений.
    """
    list_display = ('rubric', 'title', 'content', 'author', 'created_at')
    fields = (('rubric', 'author'), 'title', 'content', 'price', 'contacts', 
            'image', 'is_active')
    inlines = (AdditionalImageInline,)



# строка регистрации типов пользователей
admin.site.register(AdvUser, AdvUserAdmin)

# строка регистрации редактора надрубрик + встроенный редактор подрубрик
admin.site.register(SuperRubric, SuperRubricAdmin)

# строка регистрации редактора подрубрик
admin.site.register(SubRubric, SubRubricAdmin)

# строка регистрации редактора объявлений + встроенный редактор доп. изображений
admin.site.register(Bb, BbAdmin)
