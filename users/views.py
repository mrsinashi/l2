from django.shortcuts import redirect


def home(request):
    """Страница автоизации"""
    next = request.GET.get('next')
    return redirect('/ui/login' + ('' if not next else f"?next={next}"))
