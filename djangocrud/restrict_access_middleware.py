from django.shortcuts import redirect

class RestrictAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Código a ejecutar en cada solicitud antes de que la vista sea llamada.

        if request.user.is_authenticated and request.user.groups.filter(name='Externos_01').exists():
            if not (request.path == '/formus/formus/' or request.path == '/formus/tijera_form/' or request.path == '/logout/'):
                return redirect('/formus/formus/')

        response = self.get_response(request)

        # Código a ejecutar en cada solicitud después de que la vista es llamada.

        return response