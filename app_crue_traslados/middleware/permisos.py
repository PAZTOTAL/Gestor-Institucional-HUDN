# Added for simulating HUDN Gestor environment
class LocalPermisosMiddleware:
	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):

		if request.user.is_authenticated:
			request.user._permisos_apps_cache = {
				'crue_remisiones',
			}

		return self.get_response(request)
