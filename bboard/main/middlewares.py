# Обработчик контекста

from .models import SubRubric

def bboard_context_processor(request):
    """
    Обработчик контекста, добавляющий во все запросы к шаблонам переменную
    rubrics, содержащую список всех подрубрик. Нужен чтобы не передавать эту
    переменную во всех контроллерах.

    Также нужен, чтобы внести две переменные, хранящие страницу пагинатора и 
    поисковое слово для возврата на эти страницы после просмотра подробностей
    объявления, найденного поиском, или отображенного на странице пагинатора.
    """
    # добавляет список всех рубрик в контест всех шаблонов
    context = {}
    context['rubrics'] = SubRubric.objects.all()

    # блок кода для комфортного возврата на страницу пагинатора
    # и на список найденных объявлений после просмотра подробностей
    context['keyword'] = ''
    context['all'] = ''
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            context['keyword'] = '?keyword=' + keyword
            context['all'] = context['keyword']
    if 'page' in request.GET:
        page = request.GET['page']
        if page != '1':
            if context['all']:
                context['all'] += '&page=' + page
            else:
                context['all'] = '?page=' + page
    return context
