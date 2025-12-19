# context_processors.py
from .models import Student, Reviewer, Tag
from django.db.models import Count, Q

def user_context(request):
    """Добавляет информацию о типе пользователя в контекст"""
    context = {}
    if request.user.is_authenticated:
        try:
            student = Student.objects.get(email=request.user.email)
            context['student'] = student
            context['user_type'] = 'student'
            context['has_student_profile'] = True
        except Student.DoesNotExist:
            context['has_student_profile'] = False
        
        try:
            reviewer = Reviewer.objects.get(email=request.user.email)
            context['reviewer'] = reviewer
            context['user_type'] = 'reviewer'
            context['has_reviewer_profile'] = True
        except Reviewer.DoesNotExist:
            context['has_reviewer_profile'] = False
        
        # Если нет ни студента, ни преподавателя
        if not context.get('user_type'):
            context['user_type'] = 'unregistered'
    
    return context

def popular_tags(request):
    """Добавляет популярные теги в контекст"""
    tags = Tag.objects.filter(is_featured=True).annotate(
        active_courses_count=Count('courses', filter=Q(courses__is_active=True))
    ).order_by('-active_courses_count')[:8]
    
    return {
        'popular_tags': tags
    }