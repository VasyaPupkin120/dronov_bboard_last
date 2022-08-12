from django.shortcuts import redirect, render
from django.http import HttpResponse, Http404
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

#импорты обновления данных пользователя
from django.views.generic.edit import UpdateView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from .models import AdvUser
from .forms import ChangeUserInfoForm

# импорт для странички смены пароля
from django.contrib.auth.views import PasswordChangeView

# импорты для странички регистрации нового пользователя
from django.views.generic.edit import CreateView
from .forms import RegisterUserForm

# импорт для странички, подтверждающей регистрацию и отправку письма
from django.views.generic.base import TemplateView

# импорт для страничек активации аккаунта, контроллер user_acitvate
from django.core.signing import BadSignature
from .utilities import signer

# импорты для странички удаления аккаунта пользователя, DeleteUserView
from django.views.generic.edit import DeleteView
from django.contrib.auth import logout
from django.contrib import messages

# импорты для контроллера by_rubric - вывод объявлений по рубрикам, 
# с пагинацией и поиском
from django.core.paginator import Paginator
from django.db.models import Q
from .models import SubRubric, Bb
from .forms import SearchForm

# импорт для контроллера profile_bb_required - добавление объявлений
from .forms import BbForm, AIFormSet

# импорт и конфиг логгера
from loguru import logger

# импорт для контроллера detail - вывод подробностей об объявлении
# комментариев к объявлению и формы ввода комментария
from .models import Comment
from .forms import UserCommentForm, GuestCommentForm


def index(request):
    """
    Главная страничка. Выводится 10 последних объявлений.
    """
    bbs = Bb.objects.filter(is_active=True)[:10]
    context = {'bbs': bbs}
    return render(request, 'main/index.html', context)


def other_page(request, page):
    """
    Контроллер многих страничек с объявлениями. 
    Адрес странички (имя шаблона странички) формируется на основе 
    URL-параметра page.
    """
    try:
        template = get_template('main/' + page + '.html')
    except TemplateDoesNotExist:
        raise Http404
    return HttpResponse(template.render(request=request))


class BBLoginView(LoginView):
    """
    Класс-контроллер входа на сайт. Все основные значения - по умолчанию.
    """
    template_name = 'main/login.html'


@login_required
def profile(request):
    """
    Страничка профиля. Вывод всех объявлений текущего пользователя.
    """
    bbs = Bb.objects.filter(author=request.user.pk)
    context = {'bbs': bbs}
    return render(request, 'main/profile.html', context)


class BBLogoutView(LoginRequiredMixin, LogoutView):
    """
    Страничка успешного выхода
    """
    template_name = 'main/logout.html'


class ChangeUserInfoView(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
    """
    Страничка смены личных данных пользователя (кроме пароля)
    """
    model = AdvUser
    template_name = 'main/change_user_info.html'
    form_class = ChangeUserInfoForm
    success_url = reverse_lazy('main:profile')
    success_message = 'Данные пользователя изменены'

    def setup(self, request, *args, **kwargs):
        self.user_id = request.user.pk
        return super().setup(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, pk=self.user_id)


class BBPasswordChangeView( SuccessMessageMixin, LoginRequiredMixin, PasswordChangeView):
    """
    Страничка смены пароля пользователя
    """
    template_name = 'main/password_change.html'
    success_url = reverse_lazy('main:profile')
    success_message = 'Пароль пользователя изменен'


class RegisterUserView(CreateView):
    """
    Страничка регистрации нового пользователя.
    Перенпаравление на страничку, подтверждающую регистрацию и 
    уведомляющую об отправке письма.
    """
    model = AdvUser
    template_name = 'main/register_user.html'
    form_class = RegisterUserForm
    success_url = reverse_lazy('main:register_done')


class RegisterDoneView(TemplateView):
    """
    Страничка, подтверждающая регистрацию и уведомляющая об отправке 
    email с кодом подтверждения.
    """
    template_name = 'main/register_done.html'


def user_activate(request, sign):
    """
    Страничка активации пользователя, привязка трех шаблонов - 
    успех активации, активация выполнена ранее, ссылка скомпроментирована.
    """
    try:
        username = signer.unsign(sign)
    except BadSignature:
        return render(request, 'main/bad_signature.html')
    user = get_object_or_404(AdvUser, username=username)
    if user.is_acitvated:
        template = 'main/user_is_activated.html'
    else:
        template = 'main/activation_done.html'
        user.is_active = True
        user.is_activated = True
        user.save()
    return render(request, template)


class DeleteUserView(LoginRequiredMixin, DeleteView):
    """
    Удаление аккаунта пользователя
    """
    model = AdvUser
    template_name = 'main/delete_user.html'
    success_url = reverse_lazy('main:index')

    def setup(self, request, *args, **kwargs):
        self.user_id = request.user.pk
        return super().setup(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        logout(request)
        messages.add_message(request, messages.SUCCESS, 'Пользователь удален')
        return super().post(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, pk=self.user_id)


def by_rubric(request, pk):
    """
    Вывод списка всех обяъвлений рубрики, с пагинацией и фильтрацией 
    в полях заголовка и описания по искомому слову.
    """
    rubric = get_object_or_404(SubRubric.objects, pk=pk)
    bbs = Bb.objects.filter(is_active=True, rubric=pk)
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        q = Q(title__icontains=keyword) | Q(content__icontains=keyword)
        bbs = bbs.filter(q)
    else:
        keyword = ''
    form = SearchForm(initial={'keyword': keyword})
    paginator = Paginator(bbs, 2)
    if 'page' in request.GET:
        page_num = request.GET['page']
    else:
        page_num = 1
    page = paginator.get_page(page_num)
    context = {'rubric': rubric, 'page': page, 'bbs': page.object_list, 'form': form}
    return render(request, 'main/by_rubric.html', context)


def detail(request, rubric_pk, pk):
    """
    Отдельная страничка объявления. Вывод комментариев к объявлению.
    Форма ввода новых комментариев.
    """
    bb = get_object_or_404(Bb, pk=pk)
    ais = bb.additionalimage_set.all()
    comments = Comment.objects.filter(bb=pk, is_active=True)
    initial = {'bb': bb.pk}
    if request.user.is_authenticated:
        initial['author'] = request.user.username
        form_class = UserCommentForm
    else:
        form_class = GuestCommentForm
    form = form_class(initial=initial)
    if request.method == "POST":
        c_form = form_class(request.POST)
        if c_form.is_valid():
            c_form.save()
            messages.add_message(request, messages.SUCCESS, 'Комментарий добавлен')
        else:
            form = c_form
            messages.add_message(request, messages.WARNING, 'Комментарий не добавлен')
    context = {'bb': bb, 'ais': ais, 'comments': comments, 'form': form}
    return render(request, 'main/detail.html', context)


@login_required
def profile_bb_detail(request, pk):
    """
    Отдельная страничка объявления, видимая только зарегистрированным 
    пользователям.
    Отображает также комментарии, форму для комментариев, кнопки удаления 
    и редактирования.
    """
    bb = get_object_or_404(Bb, pk=pk)
    ais = bb.additionalimage_set.all()
    comments = Comment.objects.filter(bb=pk, is_active=True)
    initial = {'bb': bb.pk}
    initial['author'] = request.user.username
    form_class = UserCommentForm
    form = form_class(initial=initial)
    if request.method == "POST":
        c_form = form_class(request.POST)
        if c_form.is_valid():
            c_form.save()
            messages.add_message(request, messages.SUCCESS, 'Комментарий добавлен')
        else:
            form = c_form
            messages.add_message(request, messages.WARNING, 'Комментарий не добавлен')
    context = {'bb': bb, 'ais': ais, 'comments': comments, 'form': form}
    return render(request, 'main/detail_user_registered.html', context)


@login_required
def profile_bb_add(request):
    """
    Контроллер добавления нового объявления.
    """
    if request.method == "POST":
        form = BbForm(request.POST, request.FILES)
        if form.is_valid():

            bb = form.save()
            formset = AIFormSet(request.POST, request.FILES, instance=bb)
            if formset.is_valid():
                formset.save()
                messages.add_message(request, messages.SUCCESS, 'Объявление добавлено')
                return redirect('main:profile')
    else:
        form = BbForm(initial={'author': request.user.pk})
        formset = AIFormSet()
    context = {'form': form, 'formset': formset}
    return render(request, 'main/profile_bb_add.html', context)


@login_required
def profile_bb_change(request, pk):
    """
    Редактирование объявлений
    """
    bb = get_object_or_404(Bb, pk=pk)
    if request.method == "POST":
        """ ветка сохранения изменений """
        form = BbForm(request.POST, request.FILES, instance=bb)
        #FIXME не сохраняются новые изображения, если редактировать объявление
        # редактирование только текста при этом сохраняется успешно
        if form.is_valid():
            logger.debug("form valid (debug)")
            bb = form.save()
            logger.debug(f"request.POST is {request.POST}(debug)")
            logger.debug(f"request.FILES is {request.FILES}(debug)")
            formset = AIFormSet(request.POST, request.FILES, instance=bb)
            if formset.is_valid():
                logger.debug("formset valid (debug)")
                fs = formset.save()
                logger.debug(f"formset is {fs}(debug)")
                messages.add_message(request, messages.SUCCESS, 'Объявление исправлено')
                return redirect('main:profile')
    else:
        """ ветка вывода формы для редактирования """
        form = BbForm(instance=bb)
        formset = AIFormSet(instance=bb)
        context = {'form': form, 'formset': formset}
        return render(request, 'main/profile_bb_change.html', context)


@login_required
def profile_bb_delete(request, pk):
    """
    Удаление объявления
    """
    bb = get_object_or_404(Bb, pk=pk)
    if request.method == "POST":
        bb.delete()
        messages.add_message(request, messages.SUCCESS, 'Объявление удалено')
        return redirect('main:profile')
    else:
        context = {'bb': bb}
        return render(request, 'main/profile_bb_delete.html', context)
