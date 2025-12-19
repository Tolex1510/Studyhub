from django.contrib import admin
from .models import *

# Register your models here.
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    list_filter = ('created_at', 'title', 'difficulty_level', 'is_active')
    search_fields = ('title', 'description')


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    list_filter = ('created_at', 'title', 'course')
    search_fields = ('title', 'description')

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    list_filter = ('created_at', 'title', 'module')
    search_fields = ('title', 'description')

@admin.register(Reviewer)
class ReviewerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'is_approved')
    list_filter = ('last_name','status')
    search_fields = ('first_name', 'last_name', 'specialization')
    list_editable = ('is_approved',)

    def approve(self, request, queryset):
        for reviewer in queryset:
            reviewer.is_approved = True
            reviewer.save()
        self.message_user(request, f"{queryset.count()} преподавателей было одобрено")
    approve.short_description = "Одобрение администратором"

    actions = [approve]

@admin.register(TeacherCourse)
class TeacherCourseAdmin(admin.ModelAdmin):
    list_display = ('course', 'reviewer', 'assigned_at')
    list_filter = ('course', 'reviewer', 'assigned_at')
    search_fields = ('course', 'reviewer', 'assigned_at')

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    list_filter = ('name', 'slug', 'created_at')
    search_fields = ('name', 'slug', 'created_at')

@admin.register(CourseTag)
class CourseTagAdmin(admin.ModelAdmin):
    list_display = ('tag', 'course')
    list_filter = ('tag', 'course', 'created_at')
    search_fields = ('tag', 'course', 'created_at')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone')
    list_filter = ('first_name', 'last_name', 'email', 'phone')
    search_fields = ('first_name', 'last_name', 'email', 'phone')

@admin.register(CoursePrerequisite)
class CoursePrerequisiteAdmin(admin.ModelAdmin):
    list_display = ('course', 'required_course', 'requirement_type', 'min_score')
    list_filter = ('course', 'required_course', 'requirement_type', 'min_score')
    search_fields = ('course', 'required_course', 'requirement_type', 'min_score')
    list_editable = ('min_score', 'requirement_type')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'status', 'enrollment_date')
    list_filter = ('student', 'course', 'status', 'enrollment_date')
    search_fields = ('student', 'course', 'status', 'enrollment_date')

@admin.register(LessonCompletion)
class LessonCompletionAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'lesson', 'completed_at', 'score')
    list_filter = ('enrollment', 'lesson', 'completed_at', 'score')
    search_fields = ('enrollment', 'lesson', 'completed_at', 'score')
