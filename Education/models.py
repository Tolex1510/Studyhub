from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone, text
from django.core.exceptions import ValidationError


# Перечисления из БД
class DifficultyLevel(models.TextChoices):
    BEGINNER = 'beginner', 'Начинающий'
    INTERMEDIATE = 'intermediate', 'Средний'
    ADVANCED = 'advanced', 'Продвинутый'


class LessonType(models.TextChoices):
    LECTURE = 'lecture', 'Лекция'
    SEMINAR = 'seminar', 'Семинар'
    PRACTICE = 'practice', 'Практика'
    CONSULTATION = 'consultation', 'Консультация'
    TEST = 'test', 'Зачет'


class EnrollmentStatus(models.TextChoices):
    ACTIVE = 'active', 'Активно'
    COMPLETED = 'completed', 'Завершено'
    CANCELLED = 'cancelled', 'Отменено'
    PAUSED = 'paused', 'Приостановлено'
    WAITING_PAYMENT = 'waiting_payment', 'Ожидает оплаты'


class HomeworkStatus(models.TextChoices):
    SUBMITTED = 'submitted', 'Отправлено'
    UNDER_REVIEW = 'under_review', 'На проверке'
    APPROVED = 'approved', 'Одобрено'
    REJECTED = 'rejected', 'Отклонено'
    NEEDS_REVISION = 'needs_revision', 'Требует доработки'
    RESUBMITTED = 'resubmitted', 'Переотправлено'


class DeadlineType(models.TextChoices):
    COURSE_START = 'course_start', 'Начало курса'
    COURSE_COMPLETION = 'course_completion', 'Завершение курса'
    MODULE_COMPLETION = 'module_completion', 'Завершение модуля'
    LESSON_COMPLETION = 'lesson_completion', 'Завершение урока'
    HOMEWORK_SUBMISSION = 'homework_submission', 'Сдача домашнего задания'


class DeadlineStatus(models.TextChoices):
    ACTIVE = 'active', 'Активно'
    MISSED = 'missed', 'Просрочено'
    COMPLETED = 'completed', 'Выполнено'
    EXTENDED = 'extended', 'Продлено'
    CANCELLED = 'cancelled', 'Отменено'


class UrgencyLevel(models.TextChoices):
    LOW = 'low', 'Низкий'
    NORMAL = 'normal', 'Обычный'
    HIGH = 'high', 'Высокий'
    CRITICAL = 'critical', 'Критический'


class RequirementType(models.TextChoices):
    MANDATORY = 'mandatory', 'Обязательно'
    RECOMMENDED = 'recommended', 'Рекомендуется'
    OPTIONAL = 'optional', 'Опционально'


class UserStatus(models.TextChoices):
    ACTIVE = 'active', 'Активен'
    INACTIVE = 'inactive', 'Неактивен'
    SUSPENDED = 'suspended', 'Приостановлен'
    GRADUATED = 'graduated', 'Выпускник'


class Tag(models.Model):
    tag_id = models.AutoField(primary_key=True, auto_created=True)
    name = models.CharField(max_length=50, unique=True, verbose_name='Название тега')
    slug = models.SlugField(max_length=50, unique=True, verbose_name='URL-имя')
    description = models.TextField(blank=True, null=True, verbose_name='Описание тега')
    color = models.CharField(
        max_length=50, 
        default='#6c757d', 
        verbose_name='Цвет тега',
        help_text='Цвет в формате HEX (#FF5733)',
        unique=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    is_featured = models.BooleanField(default=False, verbose_name='Популярный тег')
    course_count = models.IntegerField(default=0, verbose_name='Количество курсов')
    
    class Meta:
        db_table = 'tags'
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['-is_featured', '-course_count', 'name']    
        
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            
            while Tag.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        
        # Обновляем счетчик курсов
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('courses_by_tag', kwargs={'tag_slug': self.slug})
    
    def get_active_courses_count(self):
        return self.courses.filter(is_active=True).count()

# Модели учебных элементов
class Course(models.Model):
    course_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255, verbose_name='Название курса')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    duration_weeks = models.PositiveIntegerField(validators=[MinValueValidator(1)], 
                                                 verbose_name='Продолжительность (недели)')
    difficulty_level = models.CharField(max_length=20, 
                                        choices=DifficultyLevel.choices, 
                                        default=DifficultyLevel.BEGINNER, 
                                        verbose_name='Уровень сложности')
    price = models.DecimalField(max_digits=10, decimal_places=2,
                                validators=[MinValueValidator(0)], verbose_name='Цена')
    complexity_level = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=1,
        verbose_name='Уровень сложности (1-5)'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    tags = models.ManyToManyField(
        Tag,
        through='CourseTag',
        through_fields=('course', 'tag'),
        related_name='courses',
        verbose_name='Теги',
        blank=True
    )

    class Meta:
        db_table = 'courses'
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        ordering = ['complexity_level', 'title']

    def __str__(self):
        return self.title

    def student_count(self):
        return self.enrollments.filter(status=EnrollmentStatus.ACTIVE).count()

    def get_duration_days(self):
        return self.duration_weeks * 7
    
    def get_tags_display(self):
        """Возвращает теги для отображения"""
        return self.tags.all()
        
    def lesson_count(self):
        return self.module_set.lesson_set.all().count()
    
    @property
    def total_active_lessons(self):
        """Общее количество активных уроков в курсе"""
        return Lesson.objects.filter(module__course=self, is_active=True).count()
    
    def get_course_progress(self, user):
        """Прогресс по курсу для пользователя в процентах"""
        if not user.is_authenticated:
            return 0
            
        total_lessons = self.total_active_lessons
        if total_lessons == 0:
            return 0
        
        try:
            enrollment = Enrollment.objects.get(student=Student.objects.get(email=user.email), course=self)
            completed_lessons = LessonCompletion.objects.filter(
                enrollment=enrollment,
                lesson__module__course=self,
                lesson__is_active=True
            ).count()
        except Enrollment.DoesNotExist:
            return 0
        
        return int((completed_lessons / total_lessons) * 100)
    
    def get_completed_lessons_count(self, user):
        """Количество завершенных уроков в курсе для пользователя"""
        if not user.is_authenticated:
            return 0
            
        try:
            enrollment = Enrollment.objects.get(student=Student.objects.get(email=user.email), course=self)
            return LessonCompletion.objects.filter(
                enrollment=enrollment,
                lesson__module__course=self,
                lesson__is_active=True
            ).count()
        except Enrollment.DoesNotExist:
            return 0
        
    def is_course_completed(self, student):
        """Проверка, завершен ли курс студентом"""
        total_lessons = self.total_active_lessons
        if total_lessons == 0:
            return False
        
        completed_lessons = self.get_completed_lessons_count(student)
        return completed_lessons == total_lessons
    
    def get_user_score(self, user):
        """Общий балл пользователя по курсу"""
        if not user.is_authenticated:
            return 0
            
        try:
            enrollment = Enrollment.objects.get(student=Student.objects.get(email=user.email), course=self)
            completions = LessonCompletion.objects.filter(
                enrollment=enrollment,
                lesson__module__course=self,
                lesson__is_active=True
            )
            total_score = sum(comp.score for comp in completions if comp.score)
            return total_score
        except Enrollment.DoesNotExist:
            return 0
    
    def get_max_possible_score(self):
        """Максимально возможный балл по курсу"""
        lessons = Lesson.objects.filter(module__course=self, is_active=True)
        return sum(lesson.max_score for lesson in lessons if lesson.max_score > 0)


class CourseTag(models.Model):
    coursetag_id = models.AutoField(primary_key=True)
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='course_tags',
        verbose_name='Курс'
    )
    tag = models.ForeignKey(
        Tag, 
        on_delete=models.CASCADE, 
        related_name='tagged_courses',
        verbose_name='Тег'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    
    class Meta:
        db_table = 'course_tags'
        verbose_name = 'Тег курса'
        verbose_name_plural = 'Теги курсов'
        unique_together = ['course', 'tag']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.course.title} - {self.tag.name}"


class Module(models.Model):
    module_id = models.AutoField(primary_key=True)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='modules',
        verbose_name='Курс'
    )
    title = models.CharField(max_length=255, verbose_name='Название модуля')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    module_order = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Порядковый номер'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    is_active = models.BooleanField(default=True, null=True, verbose_name="Активен")

    class Meta:
        db_table = 'modules'
        verbose_name = 'Модуль'
        verbose_name_plural = 'Модули'
        unique_together = ['course', 'module_order']
        ordering = ['course', 'module_order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    def lesson_count(self):
        return self.lessons.count()
    
    def get_completed_lessons_count(self, user):
        """Количество завершенных уроков для конкретного пользователя"""
        if not user.is_authenticated:
            return 0
        
        try:
            enrollment = Enrollment.objects.get(student=Student.objects.get(email=user.email), course=self.course)
            return LessonCompletion.objects.filter(
                enrollment=enrollment,
                lesson__module=self,
                lesson__is_active=True
            ).count()
        except Enrollment.DoesNotExist:
            return 0
    
    def get_module_progress(self, user):
        """Прогресс по модулю для пользователя в процентах"""
        total = self.lesson_count()
        if total == 0:
            return 0
        completed = self.get_completed_lessons_count(user)
        return int((completed / total) * 100)
    

class Lesson(models.Model):
    lesson_id = models.AutoField(primary_key=True)
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Модуль'
    )
    title = models.CharField(max_length=255, verbose_name='Название урока')
    content = models.TextField(blank=True, null=True, verbose_name='Содержание')
    lesson_type = models.CharField(
        max_length=20,
        choices=LessonType.choices,
        default=LessonType.LECTURE,
        verbose_name='Тип урока'
    )
    duration_minutes = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Длительность (минуты)'
    )
    lesson_order = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Порядковый номер'
    )
    video_url = models.URLField(verbose_name="Видео URL", default="", blank=True)
    has_homework = models.BooleanField(default=False, verbose_name='Есть домашнее задание')
    is_active = models.BooleanField(default=True, verbose_name='Активный')
    is_required = models.BooleanField(default=True, verbose_name='Обязательный')
    max_score = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=100,
        verbose_name='Максимальный балл'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        db_table = 'lessons'
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        unique_together = ['module', 'lesson_order']
        ordering = ['module', 'lesson_order']

    def __str__(self):
        return f"{self.module.title} - {self.title}"

    def save(self, *args, **kwargs):
        # Автоматическая настройка параметров в зависимости от типа урока
        if self.lesson_type == LessonType.LECTURE:
            self.has_homework = False
            self.max_score = 0
            self.is_required = True
        elif self.lesson_type == LessonType.SEMINAR:
            self.has_homework = False
            self.max_score = 0
            self.is_required = False
        elif self.lesson_type == LessonType.PRACTICE:
            self.has_homework = True
            self.max_score = 100
            self.is_required = True
        elif self.lesson_type == LessonType.CONSULTATION:
            self.has_homework = False
            self.max_score = 0
            self.is_required = False
        elif self.lesson_type == LessonType.TEST:
            self.has_homework = False
            self.max_score = 100
            self.is_required = True
        
        super().save(*args, **kwargs)
    
    @property
    def completion_count(self):
        """Количество завершений этого урока"""
        return self.completions.count()
    
    def is_completed_by_user(self, user):
        """Проверяет, завершил ли пользователь этот урок"""
        if not user.is_authenticated:
            return False
        
        try:
            enrollment = Enrollment.objects.get(student=user, course=self.module.course)
            return LessonCompletion.objects.filter(enrollment=enrollment, lesson=self).exists()
        except Enrollment.DoesNotExist:
            return False
    
    def get_user_completion(self, user):
        """Получает объект завершения урока для пользователя"""
        if not user.is_authenticated:
            return None
        
        try:
            enrollment = Enrollment.objects.get(student=user, course=self.module.course)
            return LessonCompletion.objects.filter(enrollment=enrollment, lesson=self).first()
        except Enrollment.DoesNotExist:
            return None


# Модели пользователей
class Student(models.Model):
    student_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    last_name = models.CharField(max_length=100, verbose_name='Фамилия')
    email = models.EmailField(unique=True, verbose_name='Email')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Телефон')
    registration_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации')
    date_of_birth = models.DateField(
        blank=True, 
        null=True, 
        verbose_name='Дата рождения'
    )
    status = models.CharField(
        max_length=20,
        choices=UserStatus.choices,
        default=UserStatus.ACTIVE,
        verbose_name='Статус'
    )

    class Meta:
        db_table = 'students'
        verbose_name = 'Студент'
        verbose_name_plural = 'Студенты'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def active_courses_count(self):
        return self.enrollments.filter(status=EnrollmentStatus.ACTIVE).count()

    def completed_courses_count(self):
        return self.enrollments.filter(status=EnrollmentStatus.COMPLETED).count()

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"


class Reviewer(models.Model):
    reviewer_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    last_name = models.CharField(max_length=100, verbose_name='Фамилия')
    email = models.EmailField(unique=True, verbose_name='Email')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Телефон')
    hire_date = models.DateField(
        verbose_name='Дата найма'
    )
    specialization = models.CharField(max_length=255, verbose_name='Специализация')
    status = models.CharField(
        max_length=20,
        choices=UserStatus.choices,
        default=UserStatus.ACTIVE,
        verbose_name='Статус'
    )
    is_approved = models.BooleanField(default=False, verbose_name='Одобрен администратором')

    class Meta:
        db_table = 'reviewers'
        verbose_name = 'Ревьюер'
        verbose_name_plural = 'Ревьюеры'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def current_workload(self):
        return self.homework_submissions.filter(status=HomeworkStatus.UNDER_REVIEW).count()
    
    def pending_submissions_count(self):
        return self.homework_submissions.filter(status=HomeworkStatus.UNDER_REVIEW).count()
    
    def get_teacher_courses(self):
        """Возвращает курсы, в которых преподаватель проверяет задания"""
        courses = TeacherCourse.objects.filter(reviewer_id=self.reviewer_id)
        return courses
    
    def get_course_stats(self, course):
        """Статистика преподавателя по конкретному курсу"""
        # ВЫЧИСЛЯЕМ все значения заранее
        pending_submissions = self.homework_submissions.filter(
            enrollment__course=course,
            status=HomeworkStatus.UNDER_REVIEW
        ).count()
        
        total_submissions = self.homework_submissions.filter(
            enrollment__course=course
        ).count()
        
        active_students = course.enrollments.filter(status='active').count()
        
        return {
            'pending_submissions': pending_submissions,
            'total_submissions': total_submissions,
            'active_students': active_students
        }


# Модели обучения и прогресса
class Enrollment(models.Model):
    enrollment_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='Студент'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='Курс'
    )
    enrollment_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата зачисления')
    completion_date = models.DateTimeField(blank=True, null=True, verbose_name='Дата завершения')
    status = models.CharField(
        max_length=20,
        choices=EnrollmentStatus.choices,
        default=EnrollmentStatus.ACTIVE,
        verbose_name='Статус'
    )
    overall_score = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=True,
        null=True,
        verbose_name='Общий балл'
    )

    class Meta:
        db_table = 'enrollments'
        verbose_name = 'Зачисление'
        verbose_name_plural = 'Зачисления'
        unique_together = ['student', 'course']
        ordering = ['-enrollment_date']

    def __str__(self):
        return f"{self.student} - {self.course}"

    def progress_percentage(self):
        total_lessons = Lesson.objects.filter(
            module__course=self.course,
            is_required=True
        ).count()
        
        completed_lessons = LessonCompletion.objects.filter(
            enrollment=self,
            lesson__is_required=True
        ).count()
        
        if total_lessons == 0:
            return 0
        return round((completed_lessons / total_lessons) * 100, 2)


class LessonCompletion(models.Model):
    completion_id = models.AutoField(primary_key=True)
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='completions',
        verbose_name='Зачисление'
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='completions',
        verbose_name='Урок'
    )
    completed_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата завершения')
    score = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=True,
        null=True,
        verbose_name='Балл'
    )

    class Meta:
        db_table = 'lesson_completions'
        verbose_name = 'Завершение урока'
        verbose_name_plural = 'Завершения уроков'
        unique_together = ['enrollment', 'lesson']
        ordering = ['-completed_at']

    def __str__(self):
        return f"{self.enrollment} - {self.lesson}"

    def clean(self):
        # Проверка что балл не превышает максимальный для урока
        if self.score and self.lesson.max_score > 0 and self.score > self.lesson.max_score:
            raise ValidationError(
                f'Балл ({self.score}) превышает максимальный ({self.lesson.max_score}) для этого урока'
            )
        
# Модели домашних заданий
class Homework(models.Model):
    homework_id = models.AutoField(primary_key=True)
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='homeworks',
        verbose_name='Урок'
    )
    title = models.CharField(max_length=255, verbose_name='Название задания')
    description = models.TextField(verbose_name='Описание')
    max_score = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(1000)],
        default=100,
        verbose_name='Максимальный балл'
    )
    deadline_days = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        verbose_name='Дней на выполнение'
    )
    is_optional = models.BooleanField(default=False, verbose_name='Опциональное')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        db_table = 'homeworks'
        verbose_name = 'Домашнее задание'
        verbose_name_plural = 'Домашние задания'
        ordering = ['lesson', 'created_at']

    def __str__(self):
        return self.title
    
    
class HomeworkSubmission(models.Model):
    submission_id = models.AutoField(primary_key=True)
    homework = models.ForeignKey(
        Homework,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name='Домашнее задание'
    )
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='homework_submissions',
        verbose_name='Зачисление'
    )
    reviewer = models.ForeignKey(
        Reviewer,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='homework_submissions',
        verbose_name='Проверяющий'
    )
    submission_text = models.TextField(verbose_name='Текст решения')
    attachment_url = models.URLField(max_length=500, blank=True, null=True, verbose_name='Ссылка на вложение')
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата отправки')
    score = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(1000)],
        blank=True,
        null=True,
        verbose_name='Балл'
    )
    feedback = models.TextField(blank=True, null=True, verbose_name='Обратная связь')
    reviewed_at = models.DateTimeField(blank=True, null=True, verbose_name='Дата проверки')
    status = models.CharField(
        max_length=20,
        choices=HomeworkStatus.choices,
        default=HomeworkStatus.SUBMITTED,
        verbose_name='Статус'
    )
    urgency = models.CharField(
        max_length=20,
        choices=UrgencyLevel.choices,
        default=UrgencyLevel.NORMAL,
        verbose_name='Срочность'
    )

    class Meta:
        db_table = 'homework_submissions'
        verbose_name = 'Отправленное задание'
        verbose_name_plural = 'Отправленные задания'
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.enrollment} - {self.homework}"

    def is_on_time(self):
        if not self.personal_deadline:
            return True
        return self.submitted_at <= self.personal_deadline

    def clean(self):
        if self.score and self.score > self.homework.max_score:
            raise ValidationError(
                f'Балл ({self.score}) превышает максимальный ({self.homework.max_score}) для этого задания'
            )
        if self.reviewed_at and self.reviewed_at < self.submitted_at:
            raise ValidationError('Дата проверки не может быть раньше даты отправки')
        

# # Модели сертификатов и системы требований
# class Certificate(models.Model):
#     certificate_id = models.AutoField(primary_key=True)
#     enrollment = models.OneToOneField(
#         Enrollment,
#         on_delete=models.CASCADE,
#         related_name='certificate',
#         verbose_name='Зачисление'
#     )
#     issue_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата выдачи')
#     expiration_date = models.DateTimeField(blank=True, null=True, verbose_name='Дата окончания действия')
#     verification_code = models.CharField(
#         max_length=100,
#         unique=True,
#         verbose_name='Код проверки'
#     )
#     grade_level = models.CharField(
#         max_length=20,
#         choices=DifficultyLevel.choices,
#         blank=True,
#         null=True,
#         verbose_name='Уровень оценки'
#     )

#     class Meta:
#         db_table = 'certificates'
#         verbose_name = 'Сертификат'
#         verbose_name_plural = 'Сертификаты'

#     def __str__(self):
#         return f"Сертификат {self.enrollment}"

#     def save(self, *args, **kwargs):
#         if not self.verification_code:
#             import uuid
#             self.verification_code = f"CERT-{self.enrollment_id}-{uuid.uuid4().hex[:8].upper()}"
        
#         if not self.grade_level:
#             self.grade_level = self.enrollment.course.difficulty_level
        
#         super().save(*args, **kwargs)

#     def is_valid(self):
#         if not self.expiration_date:
#             return True
#         return timezone.now() <= self.expiration_date


class CoursePrerequisite(models.Model):
    prerequisite_id = models.AutoField(primary_key=True)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='prerequisites',
        verbose_name='Курс'
    )
    required_course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='required_for_courses',
        verbose_name='Требуемый курс'
    )
    min_score = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=50,
        verbose_name='Минимальный балл'
    )
    requirement_type = models.CharField(
        max_length=20,
        choices=RequirementType.choices,
        default=RequirementType.MANDATORY,
        verbose_name='Тип требования'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        db_table = 'course_prerequisites'
        verbose_name = 'Предварительное требование'
        verbose_name_plural = 'Предварительные требования'
        unique_together = ['course', 'required_course']

    def __str__(self):
        return f"{self.course} требует {self.required_course}"

    def clean(self):
        if self.course == self.required_course:
            raise ValidationError('Курс не может требовать сам себя')
        

# class Deadline(models.Model):
#     deadline_id = models.AutoField(primary_key=True)
#     enrollment = models.ForeignKey(
#         Enrollment,
#         on_delete=models.CASCADE,
#         related_name='deadlines',
#         verbose_name='Зачисление'
#     )
#     deadline_type = models.CharField(
#         max_length=20,
#         choices=DeadlineType.choices,
#         verbose_name='Тип дедлайна'
#     )
#     target_id = models.PositiveIntegerField(blank=True, null=True, verbose_name='ID цели')
#     deadline_date = models.DateTimeField(verbose_name='Дата дедлайна')
#     status = models.CharField(
#         max_length=20,
#         choices=DeadlineStatus.choices,
#         default=DeadlineStatus.ACTIVE,
#         verbose_name='Статус'
#     )
#     urgency = models.CharField(
#         max_length=20,
#         choices=UrgencyLevel.choices,
#         default=UrgencyLevel.NORMAL,
#         verbose_name='Срочность'
#     )
#     completed_at = models.DateTimeField(blank=True, null=True, verbose_name='Дата выполнения')
#     created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

#     class Meta:
#         db_table = 'deadlines'
#         verbose_name = 'Дедлайн'
#         verbose_name_plural = 'Дедлайны'
#         ordering = ['deadline_date']

#     def __str__(self):
#         return f"{self.enrollment} - {self.deadline_type}"

#     def is_overdue(self):
#         return self.deadline_date < timezone.now() and not self.completed_at

#     def save(self, *args, **kwargs):
#         # Автоматическая установка срочности
#         now = timezone.now()
#         if self.deadline_date <= now + timezone.timedelta(days=3):
#             self.urgency = UrgencyLevel.CRITICAL
#         elif self.deadline_date <= now + timezone.timedelta(days=7):
#             self.urgency = UrgencyLevel.HIGH
#         elif self.deadline_date <= now + timezone.timedelta(days=14):
#             self.urgency = UrgencyLevel.NORMAL
#         else:
#             self.urgency = UrgencyLevel.LOW
        
#         super().save(*args, **kwargs)


class TeacherCourse(models.Model):
    teacher_course_id = models.AutoField(primary_key=True)
    reviewer = models.ForeignKey(
        Reviewer,
        on_delete=models.CASCADE,
        related_name='teacher_courses',
        verbose_name='Преподаватель'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='teacher_courses',
        verbose_name='Курс'
    )
    is_main_teacher = models.BooleanField(default=False, verbose_name='Основной преподаватель')
    assigned_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата назначения')

    class Meta:
        db_table = 'teacher_courses'
        verbose_name = 'Курс преподавателя'
        verbose_name_plural = 'Курсы преподавателей'
        unique_together = ['reviewer', 'course']

    def __str__(self):
        return f"{self.reviewer} - {self.course}"
    