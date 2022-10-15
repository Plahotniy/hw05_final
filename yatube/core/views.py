from http import HTTPStatus

from django.shortcuts import render


def page_404(request, exception):
    return render(
        request,
        'core/404.html',
        {'path': request.path},
        status=HTTPStatus.NOT_FOUND
    )


def page_403(request, reason=''):
    return render(request, 'core/403csrf.html')
