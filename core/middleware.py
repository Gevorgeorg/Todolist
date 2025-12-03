class DisableCSRFMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Отключаем CSRF для ВСЕХ запросов
        setattr(request, '_dont_enforce_csrf_checks', True)
        response = self.get_response(request)
        return response


class SocialAuthAdminFixMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Если запрос к админке - отключаем social auth
        if request.path.startswith('/admin/'):
            request.session['social_auth_disabled'] = True
        else:
            request.session['social_auth_disabled'] = False

        response = self.get_response(request)
        return response