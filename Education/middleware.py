# middleware.py
from django.utils.deprecation import MiddlewareMixin
from .models import Student, Reviewer

class UserTypeMiddleware(MiddlewareMixin):
    """Определяет тип пользователя и добавляет в request"""
    
    def process_request(self, request):
        if request.user.is_authenticated and not request.user.is_anonymous:
            try:
                Student.objects.get(email=request.user.email)
                request.user_type = 'student'
            except Student.DoesNotExist:
                try:
                    Reviewer.objects.get(email=request.user.email)
                    request.user_type = 'reviewer'
                except Reviewer.DoesNotExist:
                    request.user_type = 'unregistered'
        return None