# views.py
from venv import logger
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.db.models.query import QuerySet
from .models import *
from .forms import *

#Работает
def is_admin(user):
    return user.is_superuser

#Работает
def home(request):
    """Главная страница"""
    return render(request, 'home.html')

#Работает
def choose_registration_type(request):
    """Страница выбора типа регистрации"""
    return render(request, 'registration/choose_type.html')

#Работает
def student_register(request):
    """Регистрация студента"""
    if request.user.is_authenticated:
        messages.info(request, 'Вы уже вошли в систему.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            
            # Проверяем, нет ли уже пользователя с таким email
            if User.objects.filter(email=email).exists():
                form.add_error('email', 'Пользователь с таким email уже зарегистрирован')
            elif Student.objects.filter(email=email).exists():
                form.add_error('email', 'Студент с таким email уже зарегистрирован')
            elif Reviewer.objects.filter(email=email).exists():
                form.add_error('email', 'Преподаватель с таким email уже зарегистрирован')
            else:
                # Создаем студента
                student = form.save(commit=False)
                student.status = 'active'
                student.save()
                
                # Создаем пользователя Django
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=form.cleaned_data['password'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name']
                )
                
                # Автоматически логиним пользователя
                user = authenticate(username=email, password=form.cleaned_data['password'])
                if user is not None:
                    login(request, user)
                    messages.success(request, 'Регистрация студента прошла успешно! Добро пожаловать!')
                    return redirect('dashboard')
    else:
        form = StudentRegistrationForm()
    
    context = {
        'form': form,
        'user_type': 'student'
    }
    return render(request, 'registration/register.html', context)

#Работает
def reviewer_register(request):
    """Регистрация преподавателя"""
    if request.user.is_authenticated:
        messages.info(request, 'Вы уже вошли в систему.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ReviewerRegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            
            # Проверяем, нет ли уже пользователя с таким email
            if User.objects.filter(email=email).exists():
                form.add_error('email', 'Пользователь с таким email уже зарегистрирован')
            elif Reviewer.objects.filter(email=email).exists():
                form.add_error('email', 'Преподаватель с таким email уже зарегистрирован')
            elif Student.objects.filter(email=email).exists():
                form.add_error('email', 'Студент с таким email уже зарегистрирован')
            else:
                # Создаем преподавателя (не одобренного по умолчанию)
                reviewer = form.save(commit=False)
                reviewer.status = 'active'
                reviewer.is_approved = False  # Требует одобрения администратора
                reviewer.save()
                
                # Создаем пользователя Django
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=form.cleaned_data['password'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    is_staff=False  # Не даем права администратора по умолчанию
                )
                
                # Автоматически логиним пользователя
                user = authenticate(username=email, password=form.cleaned_data['password'])
                if user is not None:
                    login(request, user)
                    messages.success(
                        request, 
                        'Регистрация преподавателя прошла успешно! '
                        'Ваш аккаунт ожидает одобрения администратора.'
                    )
                    return redirect('dashboard')
    else:
        form = ReviewerRegistrationForm()
    
    context = {
        'form': form,
        'user_type': 'reviewer'
    }
    return render(request, 'registration/register.html', context)

#Работает
# Вспомогательная функция для проверки, является ли пользователь студентом
def is_student(user):
    """Проверяет, есть ли у пользователя профиль студента"""
    return Student.objects.filter(email=user.email).exists()

#Работает
@login_required
def dashboard(request):
    """Универсальный личный кабинет с приоритетом преподавателя"""
    user = request.user
    
    # Проверяем, является ли пользователь преподавателем (приоритет)
    try:
        reviewer = Reviewer.objects.get(email=user.email)
        if reviewer.is_approved:
            return reviewer_dashboard(request, reviewer)
        else:
            # Если преподаватель не одобрен, проверяем студента
            try:
                student = Student.objects.get(email=user.email)
                messages.info(request, 'Ваш аккаунт преподавателя ожидает одобрения. Пока доступен студенческий аккаунт.')
                return student_dashboard(request, student)
            except Student.DoesNotExist:
                messages.warning(request, 'Ваш аккаунт преподавателя ожидает одобрения администратора.')
                return reviewer_dashboard(request, reviewer)
    except Reviewer.DoesNotExist:
        pass
    
    # Проверяем, является ли пользователь студентом
    try:
        student = Student.objects.get(email=user.email)
        return student_dashboard(request, student)
    except Student.DoesNotExist:
        pass
    
    # Если нет ни студента, ни преподавателя - предлагаем завершить регистрацию
    messages.warning(request, 'Пожалуйста, завершите регистрацию.')
    return redirect('choose_registration_type')

#Работает
def student_dashboard(request, student):
    """Дашборд для студента"""
    # Оптимизированный запрос для прогресса
    enrollments_with_progress = student.enrollments.select_related('course').annotate(
        total_lessons=Count('course__modules__lessons', filter=Q(course__modules__lessons__is_required=True)),
        completed_lessons=Count('completions', filter=Q(completions__lesson__is_required=True))
    )
    
    # Добавляем процент прогресса
    for enrollment in enrollments_with_progress:
        if enrollment.total_lessons > 0:
            enrollment.progress_percentage = round((enrollment.completed_lessons / enrollment.total_lessons) * 100, 2)
        else:
            enrollment.progress_percentage = 0
    
    context = {
        'student': student,
        'reviewer': None,
        'active_enrollments': enrollments_with_progress.filter(status='active'),
        'completed_enrollments': enrollments_with_progress.filter(status='completed'),
        'user_type': 'student'
    }
    return render(request, 'dashboard/student_dashboard.html', context)

#Работает
def reviewer_dashboard(request, reviewer):
    try:
        # Используем методы модели
        pending_submissions = reviewer.pending_submissions_count()
        total_submissions = reviewer.homework_submissions.count()
        
        # Последние задания
        recent_submissions = reviewer.homework_submissions.filter(
            status=HomeworkStatus.UNDER_REVIEW
        ).select_related(
            'homework__lesson__module__course',
            'enrollment__student'
        )[:5]
        
        # Курсы преподавателя через метод модели
        teacher_courses = reviewer.get_teacher_courses()
        # ВЫЧИСЛЯЕМ ВСЕ ДАННЫЕ ЗАРАНЕЕ для шаблона
        courses_with_stats = []
        for teacher_course in teacher_courses:
            # Вычисляем количество активных студентов
            course = Course.objects.get(course_id=teacher_course.course_id)
            active_students_count = course.enrollments.filter(status='active').count()
            
            # Вычисляем задания на проверку в этом курсе
            pending_in_course = reviewer.homework_submissions.filter(
                enrollment__course=course,
                status=HomeworkStatus.UNDER_REVIEW
            ).count()
            
            # Общее количество submission'ов в курсе
            total_in_course = reviewer.homework_submissions.filter(
                enrollment__course=course
            ).count()
            
            courses_with_stats.append({
                'course': course,
                'stats': {
                    'active_students_count': active_students_count,  # Уже вычисленное значение
                    'pending_in_course': pending_in_course,          # Уже вычисленное значение
                    'total_in_course': total_in_course               # Уже вычисленное значение
                }
            })
        
        context = {
            'student': None,
            'reviewer': reviewer,
            'pending_submissions': pending_submissions,
            'total_submissions': total_submissions,
            'recent_submissions': recent_submissions,
            'courses_with_stats': courses_with_stats,
            'user_type': 'reviewer'
        }
        return render(request, 'dashboard/reviewer_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error in reviewer_dashboard_final: {str(e)}")
        
        # Резервный контекст
        context = {
            'student': None,
            'reviewer': reviewer,
            'pending_submissions': reviewer.homework_submissions.filter(
                status=HomeworkStatus.UNDER_REVIEW
            ).count(),
            'total_submissions': reviewer.homework_submissions.count(),
            'recent_submissions': [],
            'courses_with_stats': [],
            'user_type': 'reviewer'
        }
        return render(request, 'dashboard/reviewer_dashboard.html', context)


@login_required
def student_stats(request):
    """Статистика студента"""
    # Получаем все зачисления
    enrollments = Enrollment.objects.filter(student=Student.objects.get(email=request.user.email)).select_related('course')
    
    # Общая статистика
    total_courses = enrollments.count()
    completed_courses = sum(1 for e in enrollments if e.course.is_course_completed(request.user))
    
    # Подсчет уроков
    total_lessons_completed = 0
    total_score = 0
    max_possible_score = 0
    
    for enrollment in enrollments:
        total_lessons_completed += enrollment.completed_lessons_count
        total_score += enrollment.total_score
        max_possible_score += enrollment.course.get_max_possible_score()
    
    # Последние завершенные уроки
    recent_completions = LessonCompletion.objects.filter(
        enrollment__student=request.user
    ).select_related('lesson', 'lesson__module', 'lesson__module__course').order_by('-completed_at')[:10]
    
    context = {
        'total_courses': total_courses,
        'completed_courses': completed_courses,
        'total_lessons_completed': total_lessons_completed,
        'total_score': total_score,
        'max_possible_score': max_possible_score,
        'recent_completions': recent_completions,
        'title': 'Моя статистика'
    }
    return render(request, 'courses/student_stats.html', context)

#Работает
@login_required
def student_courses(request):
    """Страница курсов"""
    try:
        student = Student.objects.get(email=request.user.email)
    except (Student.DoesNotExist, AttributeError):
        return redirect('home')

    active_courses = Course.objects.filter(is_active=True)
    my_courses = []
    for active_course in active_courses:
        try:
            enrollment = Enrollment.objects.get(student=student, course=active_course)
            my_courses.append(active_course)
        except Enrollment.DoesNotExist:
            pass

    context = {'my_courses': my_courses}
        

    return render(request, 'courses/student_courses.html', context)


#Работает
def course_list(request):
    """Публичный список всех активных курсов с поиском и фильтрацией"""
    courses = Course.objects.filter(is_active=True).prefetch_related('tags', 'modules')
    
    # Форма поиска
    search_form = CourseSearchForm(request.GET)
    tag_filter_form = TagFilterForm(request.GET)
    
    # Применяем фильтры
    query = request.GET.get('query', '')
    selected_tags = request.GET.getlist('tags')
    difficulty = request.GET.get('difficulty', '')
    
    if query:
        courses = courses.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()
    
    if selected_tags:
        courses = courses.filter(tags__in=selected_tags).distinct()
    
    if difficulty:
        courses = courses.filter(difficulty_level=difficulty)
    
    # Получаем популярные теги для сайдбара
    popular_tags = Tag.objects.filter(is_featured=True).annotate(
        active_courses_count=Count('courses', filter=Q(courses__is_active=True))
    ).order_by('-active_courses_count')[:10]
    
    # Статистика для отображения
    total_courses = courses.count()

    total_lessons = {}
    for course in courses:
        lesson_counter = 0
        for module in course.modules.all():
            lesson_counter += module.lessons.count()
        total_lessons[course] = lesson_counter

    print(total_lessons)
    context = {
        'courses': courses,
        'total_lessons': total_lessons,
        'search_form': search_form,
        'tag_filter_form': tag_filter_form,
        'popular_tags': popular_tags,
        'total_courses': total_courses,
        'query': query,
        'selected_tags': selected_tags,
        'active_tab': 'courses'
    }
    return render(request, 'courses/course_list.html', context)

#Работает
def courses_by_tag(request, tag_slug):
    """Список курсов по конкретному тегу"""
    tag = get_object_or_404(Tag, slug=tag_slug)
    courses = Course.objects.filter(
        tags=tag, 
        is_active=True
    ).prefetch_related('tags', 'modules', 'enrollments')
    
    # Похожие теги
    similar_tags = Tag.objects.filter(
        courses__in=courses
    ).exclude(pk=tag.pk).annotate(
        common_courses=Count('pk')
    ).order_by('-common_courses')[:5]
    
    context = {
        'tag': tag,
        'courses': courses,
        'similar_tags': similar_tags,
        'title': f'Курсы с тегом: {tag.name}'
    }
    return render(request, 'courses/courses_by_tag.html', context)

#Работает
def tag_cloud(request):
    """Облако тегов для публичного доступа"""
    tags = Tag.objects.annotate(
        tag_course_count=Count('courses', filter=Q(courses__is_active=True))  # Изменили название
    ).filter(tag_course_count__gt=0).order_by('-tag_course_count')
    
    # Группируем теги по популярности для разного размера шрифта
    if tags:
        max_count = tags[0].tag_course_count  # Обновили название
        for tag in tags:
            if max_count > 0:
                # Вычисляем размер шрифта от 0.8em до 2em
                tag.font_size = 0.8 + (tag.tag_course_count / max_count) * 1.2  # Обновили название
            else:
                tag.font_size = 1
    
    context = {
        'tags': tags,
        'title': 'Облако тегов'
    }
    return render(request, 'courses/tag_cloud.html', context)

#Работает
def course_detail(request, course_id):
    """Детальная страница курса (доступна без регистрации)"""
    course = get_object_or_404(Course, pk=course_id, is_active=True)
    
    course_info = {
        'course': course,
        'is_enrolled': False,
        'can_enroll': False,
        'is_authenticated': request.user.is_authenticated,
        'needs_student_profile': False,
        'missing_requirements': {'mandatory': [], 'recommended': []}
    }
    
    if request.user.is_authenticated:
        try:
            student = Student.objects.get(email=request.user.email)
            # Проверяем, записан ли студент
            try:
                enrollment = Enrollment.objects.get(student=student, course=course)
                course_info['is_enrolled'] = True
                course_info['enrollment_status'] = enrollment.status
            except Enrollment.DoesNotExist:
                course_info['is_enrolled'] = False
            
            # Проверяем возможность записи
            if not course_info['is_enrolled']:
                can_enroll, missing_requirements = check_course_prerequisites(student, course)
                course_info['can_enroll'] = can_enroll
                course_info['missing_requirements'] = missing_requirements
                
        except Student.DoesNotExist:
            # У пользователя нет профиля студента
            course_info['needs_student_profile'] = True
    
    # Получаем модули и уроки курса
    modules = course.modules.all().prefetch_related('lessons').order_by('module_order')
    
    # Статистика курса
    course_stats = {
        'total_modules': modules.count(),
        'total_lessons': Lesson.objects.filter(module__course=course).count(),
        'active_students': course.enrollments.filter(status='active').count(),
        'completed_students': course.enrollments.filter(status='completed').count(),
    }
    
    context = {
        'course': course,
        'modules': modules,
        'course_stats': course_stats,
        **course_info  # Добавляем всю информацию о статусе
    }
    
    return render(request, 'courses/course_detail.html', context)

#Работает
@login_required
def enroll_in_course(request, course_id):
    """Зачисление студента на курс (только для аутентифицированных)"""
    course = get_object_or_404(Course, pk=course_id, is_active=True)
    
    try:
        student = Student.objects.get(email=request.user.email)
    except Student.DoesNotExist:
        messages.error(request, 'Для записи на курс необходимо завершить регистрацию студента.')
        return redirect('student_register')
    
    # Проверяем предварительные требования
    can_enroll, missing_requirements = check_course_prerequisites(student, course)
    
    if not can_enroll:
        messages.error(request, 'Не выполнены предварительные требования для этого курса.')
        return redirect('course_detail', course_id=course_id)
    
    # Проверяем, не записан ли студент уже
    if Enrollment.objects.filter(student=student, course=course).exists():
        messages.warning(request, 'Вы уже записаны на этот курс.')
        return redirect('course_detail', course_id=course_id)
    
    # Создаем зачисление
    enrollment = Enrollment.objects.create(
        student=student,
        course=course,
        enrollment_date=timezone.now(),
        status='active'
    )
    
    messages.success(request, f'Вы успешно записаны на курс "{course.title}"!')
    return redirect('dashboard')

#Работает?
def check_course_prerequisites(student, course):
    """
    Проверяет, выполнены ли все предварительные требования для курса
    Возвращает (can_enroll: bool, missing_requirements: dict)
    """
    # Получаем все обязательные предварительные требования
    prerequisites = CoursePrerequisite.objects.filter(
        course=course,
        requirement_type='mandatory'
    )
    
    missing_requirements = []
    
    for prereq in prerequisites:
        required_course = prereq.required_course
        min_score = prereq.min_score
        
        # Проверяем, завершил ли студент требуемый курс
        try:
            enrollment = Enrollment.objects.get(
                student=student,
                course=required_course,
                status='completed'
            )
            
            # Проверяем минимальный балл, если требуется
            if min_score > 0:
                if enrollment.overall_score is None or enrollment.overall_score < min_score:
                    missing_requirements.append({
                        'course': required_course,
                        'reason': f'Необходимый балл: {min_score}, ваш балл: {enrollment.overall_score or "не оценен"}'
                    })
            
        except Enrollment.DoesNotExist:
            missing_requirements.append({
                'course': required_course,
                'reason': 'Курс не завершен'
            })
    
    # Проверяем рекомендованные требования (только для информации)
    recommended_prerequisites = CoursePrerequisite.objects.filter(
        course=course,
        requirement_type='recommended'
    )
    
    recommended_info = []
    for prereq in recommended_prerequisites:
        required_course = prereq.required_course
        try:
            Enrollment.objects.get(
                student=student,
                course=required_course,
                status='completed'
            )
            # Студент выполнил рекомендованное требование
        except Enrollment.DoesNotExist:
            recommended_info.append(required_course)
    
    can_enroll = len(missing_requirements) == 0
    
    return can_enroll, {
        'mandatory': missing_requirements,
        'recommended': recommended_info
    }

#Работает
def custom_login(request):
    """Кастомная страница входа с проверкой типа пользователя"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            # Получаем аутентифицированного пользователя
            user = form.get_user()
            
            # Логиним пользователя
            login(request, user)
            
            # Проверяем тип пользователя и показываем соответствующее сообщение
            try:
                student = Student.objects.get(email=user.email)
                messages.success(request, f'Добро пожаловать, {student.get_full_name()}!')
            except Student.DoesNotExist:
                try:
                    reviewer = Reviewer.objects.get(email=user.email)
                    if reviewer.is_approved:
                        messages.success(request, f'Добро пожаловать, преподаватель {reviewer.get_full_name()}!')
                    else:
                        messages.warning(request, f'Добро пожаловать! Ваш аккаунт преподавателя ожидает одобрения.')
                except Reviewer.DoesNotExist:
                    messages.info(request, 'Добро пожаловать! Завершите регистрацию.')
            
            # Перенаправляем на next или dashboard
            next_url = request.POST.get('next', 'dashboard')
            return redirect(next_url)
    else:
        form = CustomAuthenticationForm()
    
    context = {
        'form': form,
        'next': request.GET.get('next', 'dashboard')
    }
    return render(request, 'registration/login.html', context)

#Работает
@login_required
@user_passes_test(is_admin)
def tag_management(request):
    """Управление тегами"""
    tags = Tag.objects.all().prefetch_related('tagged_courses')
    
    # Статистика по тегам
    tags_with_stats = []
    for tag in tags:
        stats = {
            'course_count': tag.tagged_courses.count(),
            'active_courses': tag.tagged_courses.filter(course__is_active=True).count(),
        }
        tags_with_stats.append({
            'tag': tag,
            'stats': stats
        })
    
    context = {
        'tags_with_stats': tags_with_stats,
        'active_tab': 'tags'
    }
    return render(request, 'courses/tag_management.html', context)

@login_required
@user_passes_test(is_admin)
def tag_create(request):
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            new_form = request.POST.copy()
            for i in range(1, Tag.objects.count() + 1):
                try:
                    tag = Tag.objects.get(tag_id = i)
                except:
                    new_form["tag_id"] = i
                    break
            if not new_form["tag_id"]:
                new_form['tag_id'] = Tag.objects.count() + 1
            form = TagForm(new_form)
            print(form.data['tag_id'])
            tag = form.save()
            messages.success(request, f'Тег "{tag.name}" успешно создан!')
            return redirect('tag_management')
    else:
        form = TagForm()

    context = {
        "form": form
    }
    return render(request, 'courses/tag_edit.html', context)

@login_required
@user_passes_test(is_admin)
def tag_edit(request, tag_id):
    """Редактирование тега"""
    tag = get_object_or_404(Tag, pk=tag_id)
    
    if request.method == 'POST':
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            messages.success(request, f'Тег "{tag.name}" успешно обновлен!')
            return redirect('tag_management')
        print(form.errors)
    else:
        form = TagForm(instance=tag)
    
    context = {
        'form': form,
        'tag': tag,
        'title': f'Редактирование тега: {tag.name}'
    }
    return render(request, 'courses/tag_edit.html', context)


@login_required
@user_passes_test(is_admin)
def tag_delete(request, tag_id):
    """Удаление тега"""
    tag = get_object_or_404(Tag, pk=tag_id)
    
    if request.method == 'POST':
        tag_name = tag.name
        tag.delete()
        messages.success(request, f'Тег "{tag_name}" успешно удален!')
        return redirect('tag_management')
    
    context = {
        'tag': tag
    }
    return render(request, 'courses/tag_confirm_delete.html', context)


#Работает
@login_required
def course_create(request):
    """Создание нового курса"""
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user
            course.save()
            form.save_m2m()  # Для тегов
            messages.success(request, f'Курс "{course.title}" успешно создан!')
            teacher_course = TeacherCourse(
                reviewer=Reviewer.objects.get(email=request.user.email),
                course=course,
                is_main_teacher=True,
            )
            teacher_course.save()
            return redirect('dashboard')
    else:
        form = CourseForm()
    
    context = {
        'form': form,
        'title': 'Создание курса'
    }
    return render(request, 'courses/course_form.html', context)


#Работает
@login_required
def module_create(request):
    """Создание нового модуля"""
    course = None
    
    
    if request.method == 'POST':
        form = ModuleForm(request.POST)
        try:
            course = Course.objects.get(course_id=form.data['course'])
        except Course.DoesNotExist:
            messages.error(request, 'Курс не найден или у вас нет прав доступа')
            return redirect('dashboard')
        new_form = request.POST.copy()
        new_form['course'] = course
        form = ModuleForm(new_form)
        if form.is_valid():
            module = form.save()
            messages.success(request, f'Модуль "{module.title}" успешно создан!')
            return redirect('course_manage', pk=module.course.course_id)
        else:
            print(form.errors)
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
    else:
        # Для GET запроса инициализируем форму с выбранным курсом
        initial = {}
        if course:
            initial['course'] = course  # Передаем ID курса в initial
        
        form = ModuleForm(initial=initial)
    
    # Фильтруем курсы только текущего преподавателя
    teacher_courses = TeacherCourse.objects.filter(reviewer=Reviewer.objects.get(email=request.user.email))
    courses = Course.objects.filter(course_id__in=teacher_courses.values_list('course'))
    form.fields['course'].queryset = courses    
    context = {
        'form': form,
        'title': 'Создание модуля',
        'course': course  # Передаем объект курса в шаблон
    }
    return render(request, 'courses/module_form.html', context)


#Работает
@login_required
def lesson_create(request):
    """Создание нового урока"""
    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES)
        try:
            module = Module.objects.get(module_id=form.data['module'])
        except Module.DoesNotExist:
            messages.error(request, 'Курс не найден или у вас нет прав доступа')
            return redirect('dashboard')
        new_form = request.POST.copy()
        new_form['module'] = module
        form = LessonForm(new_form)
        print(form.data)
        if form.is_valid():
            print("valid")
            lesson = form.save()
            messages.success(request, f'Урок "{lesson.title}" успешно создан!')
            return redirect('dashboard')
        print(form.errors)
    else:
        form = LessonForm()
        # Фильтруем модули только курсов текущего преподавателяteacher_courses = TeacherCourse.objects.filter(reviewer=Reviewer.objects.get(email=request.user.email))
        teacher_courses = TeacherCourse.objects.filter(reviewer=Reviewer.objects.get(email=request.user.email))
        courses = Course.objects.filter(course_id__in=teacher_courses.values_list('course'))
        modules = Module.objects.filter(course__in=courses)
        form.fields['module'].queryset = modules
    
    context = {
        'form': form,
        'title': 'Создание урока'
    }
    return render(request, 'courses/lesson_form.html', context)


@login_required
def course_manage(request, pk):
    """Управление курсом - детальная страница с модулями и уроками"""
    course = get_object_or_404(Course, course_id=pk)
    modules = course.modules.all().prefetch_related('lessons')
    
    context = {
        'course': course,
        'modules': modules,
        'title': f'Управление курсом: {course.title}'
    }
    return render(request, 'courses/course_manage.html', context)

@login_required
def course_delete(request, pk):
    """Удаление курса"""
    course = get_object_or_404(Course, course_id=pk)
    if request.method == 'POST':
        course_title = course.title
        course.delete()
        messages.success(request, f'Курс "{course_title}" успешно удален!')
        return redirect('dashboard')
    return redirect('course_edit', course_id=pk)

@login_required
def module_delete(request, pk):
    """Удаление модуля"""
    module = get_object_or_404(Module, module_id=pk)
    course_id = module.course.course_id
    if request.method == 'POST':
        module_title = module.title
        module.delete()
        messages.success(request, f'Модуль "{module_title}" успешно удален!')
        return redirect('course_manage', pk=course_id)
    return redirect('module_edit', module_id=pk)

@login_required
def lesson_delete(request, pk):
    """Удаление урока"""
    lesson = get_object_or_404(Lesson, lesson_id=pk)
    course_id = lesson.module.course.course_id
    if request.method == 'POST':
        lesson_title = lesson.title
        lesson.delete()
        messages.success(request, f'Урок "{lesson_title}" успешно удален!')
        return redirect('course_manage', pk=course_id)
    return redirect('lesson_edit', lesson_id=pk)


@login_required
def course_edit(request, pk):
    """Редактирование существующего курса"""
    course = get_object_or_404(Course, pk=pk)
    reviewer = Reviewer.objects.get(email=request.user.email)
    try:
        teacher_course = TeacherCourse.objects.get(reviewer=reviewer,course=course)
    except:
        return HttpResponseForbidden("У вас нет прав для редактирования этого курса")
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        print(form.data)
        if form.is_valid():
            course = form.save()
            for tag in Tag.objects.all():
                tag.course_count = tag.courses.count()
                tag.save()
            messages.success(request, f'Курс "{course.title}" успешно обновлен!')
            return redirect('course_manage', pk=course.course_id)
        print(form.errors)
    else:
        form = CourseForm(instance=course)
    
    context = {
        'form': form,
        'course': course,
        'title': f'Редактирование курса: {course.title}'
    }
    return render(request, 'courses/course_edit.html', context)

@login_required
def module_edit(request, pk):
    """Редактирование существующего модуля"""
    module = get_object_or_404(Module, module_id=pk)
    reviewer = None
    try:
        reviewer = Reviewer.objects.get(email=request.user.email)
        teacher_course = TeacherCourse.objects.get(reviewer=reviewer,course=module.course)
    except:
        return HttpResponseForbidden("У вас нет прав для редактирования этого курса")
    
    if request.method == 'POST':
        new_form = request.POST.copy()
        new_form['course'] = module.course
        form = ModuleForm(new_form, instance=module)
        if form.is_valid():
            module = form.save()
            messages.success(request, f'Модуль "{module.title}" успешно обновлен!')
            return redirect('course_manage', pk=module.course.course_id)
    else:
        form = ModuleForm(instance=module)
        # Фильтруем курсы только текущего преподавателя
        teacher_course = TeacherCourse.objects.filter(reviewer=reviewer)
        form.fields['course'].queryset = Course.objects.filter(course_id__in=teacher_course.values_list('course'))
    
    context = {
        'form': form,
        'module': module,
        'course': module.course,
        'title': f'Редактирование модуля: {module.title}'
    }
    return render(request, 'courses/module_form.html', context)

@login_required
def lesson_edit(request, pk):
    """Редактирование существующего урока"""
    lesson = get_object_or_404(Lesson, lesson_id=pk)
    reviewer = Reviewer.objects.get(email=request.user.email)
    
    try:
        teacher_course = TeacherCourse.objects.get(reviewer=reviewer,course=lesson.module.course)
    except:
        return HttpResponseForbidden("У вас нет прав для редактирования этого курса")
    
    if request.method == 'POST':
        new_form = request.POST.copy()
        new_form['module'] = lesson.module
        form = LessonForm(new_form, request.FILES, instance=lesson)
        if form.is_valid():
            lesson = form.save()
            messages.success(request, f'Урок "{lesson.title}" успешно обновлен!')
            return redirect('course_manage', pk=lesson.module.course.course_id)
        print(form.errors)
    else:
        form = LessonForm(instance=lesson)
        teacher_course = TeacherCourse.objects.filter(reviewer=reviewer)
        form.fields['module'].queryset = Module.objects.filter(course_id__in=teacher_course.values_list('course'))
    
    context = {
        'form': form,
        'lesson': lesson,
        'module': lesson.module,
        'title': f'Редактирование урока: {lesson.title}'
    }
    return render(request, 'courses/lesson_form.html', context)

#Работает
@login_required
def course_modules(request, course_id):
    # Проверяем, записан ли студент на курс
    enrollment = get_object_or_404(
        Enrollment, 
        course_id=course_id, 
        student=Student.objects.get(email=request.user.email)
    )
    
    course = enrollment.course
    # Получаем модули курса
    modules = course.modules.order_by('module_order')
    

    total_lessons = {}
    lesson_counter = 0
    modules = Module.objects.filter(course=course)
    module_progress = {}
    for module in modules:
        lesson_counter += module.lessons.count()
        module_progress[module.module_id] = module.get_module_progress(request.user)
    total_lessons[course] = lesson_counter

    is_completed = course.is_course_completed(request.user)
    author = None
    try:
        teacher_course = TeacherCourse.objects.get(course=course)
        author = teacher_course.reviewer
    except:
        pass
    context = {
        'course': course,
        'enrollment': enrollment,
        'modules': modules,  # modules уже содержат все необходимые данные
        'course_progress': course.get_course_progress(request.user),  # процент завершения
        'completed_course_lessons': course.get_completed_lessons_count(request.user),
        'total_course_lessons': course.total_active_lessons,
        'total_score': course.get_user_score(request.user),
        'max_score': course.get_max_possible_score(),
        'is_course_completed': course.is_course_completed(request.user),
        'title': f'Модули курса: {course.title}',
        'author': author
    }
    return render(request, 'courses/course_modules.html', context)


#Работает
@login_required
def lesson_detail(request, lesson_id):
    """Детальная страница урока для студента - упрощенная версия"""
    lesson = get_object_or_404(Lesson, lesson_id=lesson_id, is_active=True)
    
    # Проверяем, записан ли студент на курс
    enrollment = get_object_or_404(
        Enrollment,
        course=lesson.module.course,
        student=Student.objects.get(email=request.user.email)
    )

    completion = None
    try:
        completion = LessonCompletion.objects.get(
            enrollment=enrollment,
            lesson=lesson
        )
    except LessonCompletion.DoesNotExist:
        pass
    
    # Получаем соседние уроки
    next_lesson = Lesson.objects.filter(
        module=lesson.module,
        lesson_order__gt=lesson.lesson_order,
        is_active=True
    ).order_by('lesson_order').first()
    
    prev_lesson = Lesson.objects.filter(
        module=lesson.module,
        lesson_order__lt=lesson.lesson_order,
        is_active=True
    ).order_by('-lesson_order').first()
    
    # Получаем все уроки модуля
    module_lessons = Lesson.objects.filter(
        module=lesson.module,
        is_active=True
    ).order_by('lesson_order')
    
    context = {
        'lesson': lesson,
        'enrollment': enrollment,
        'completion': completion,
        'next_lesson': next_lesson,
        'prev_lesson': prev_lesson,
        'module_lessons': module_lessons,
        'title': lesson.title
    }
    return render(request, 'courses/lesson_detail.html', context)

@login_required
def complete_lesson(request, lesson_id):
    """Отметить урок как завершенный"""
    if request.method == 'POST':
        lesson = get_object_or_404(Lesson, lesson_id=lesson_id, is_active=True)
        
        # Проверяем, записан ли студент на курс
        enrollment = get_object_or_404(
            Enrollment,
            course=lesson.module.course,
            student=Student.objects.get(email=request.user.email)
        )
        
        # Проверяем, не завершен ли уже урок
        if LessonCompletion.objects.filter(enrollment=enrollment, lesson=lesson).exists():
            messages.info(request, 'Вы уже завершили этот урок.')
            return redirect('lesson_detail', lesson_id=lesson_id)
        
        # Получаем балл из формы, если есть
        score = request.POST.get('score')
        if score:
            try:
                score = int(score)
                if score < 0 or score > 100:
                    score = None
                if lesson.max_score > 0 and score > lesson.max_score:
                    score = None
            except (ValueError, TypeError):
                score = None
        
        # Создаем запись о завершении
        completion = LessonCompletion.objects.create(
            enrollment=enrollment,
            lesson=lesson,
            score=score
        )
        
        messages.success(request, f'Урок "{lesson.title}" успешно завершен!')
        
        # Проверяем, завершен ли теперь модуль
        module = lesson.module
        module_completed = module.get_module_progress(request.user) == 100
        
        if module_completed:
            messages.success(request, f'Поздравляем! Вы завершили модуль "{module.title}"!')
        
        # Проверяем, завершен ли теперь курс
        course_completed = lesson.module.course.is_course_completed(request.user)
        if course_completed:
            messages.success(request, f'🎉 Поздравляем! Вы завершили курс "{lesson.module.course.title}"!')
        
        # Перенаправляем на следующий урок или список модулей
        next_lesson = Lesson.objects.filter(
            module=lesson.module,
            lesson_order__gt=lesson.lesson_order,
            is_active=True
        ).order_by('lesson_order').first()
        
        if next_lesson:
            return redirect('lesson_detail', lesson_id=next_lesson.lesson_id)
        else:
            return redirect('dashboard')
    
    return redirect('lesson_detail', lesson_id=lesson_id)


@login_required
def uncomplete_lesson(request, lesson_id):
    """Отменить завершение урока"""
    if request.method == 'POST':
        lesson = get_object_or_404(Lesson, lesson_id=lesson_id, is_active=True)
        
        # Проверяем, записан ли студент на курс
        enrollment = get_object_or_404(
            Enrollment,
            course=lesson.module.course,
            student=Student.objects.get(email=request.user.email)
        )
        
        # Удаляем запись о завершении
        deleted_count, _ = LessonCompletion.objects.filter(
            enrollment=enrollment,
            lesson=lesson
        ).delete()
        
        if deleted_count > 0:
            messages.success(request, f'Завершение урока "{lesson.title}" отменено.')
        else:
            messages.info(request, 'Этот урок еще не был завершен.')
        
        return redirect('lesson_detail', lesson_id=lesson_id)
    
    return redirect('course_modules', course_id=lesson.module.course.course_id)