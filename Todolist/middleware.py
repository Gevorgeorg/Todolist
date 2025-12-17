
class SocialAuthAdminFixMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.path.startswith('/admin/'):
            request.session['social_auth_disabled'] = True
        else:
            request.session['social_auth_disabled'] = False

        response = self.get_response(request)
        return response