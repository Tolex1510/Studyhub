"""
URL configuration for ProjectDB project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from Education import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),

    #Работает
    path('auth/', include('django.contrib.auth.urls')),
    path('register/type/', views.choose_registration_type, name='choose_registration_type'),
    path('register/student/', views.student_register, name='student_register'),
    path('register/reviewer/', views.reviewer_register, name='reviewer_register'),
    path('login/', views.custom_login, name='login'),

    #Работает
    path('courses/', views.course_list, name='course_list'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('courses/<int:course_id>/enroll/', views.enroll_in_course, name='enroll_in_course'),
    
    #Работает
    path('courses/tag/<slug:tag_slug>/', views.courses_by_tag, name='courses_by_tag'),
    path('courses/tags/', views.tag_cloud, name='tag_cloud'),
        
    #Работает (кроме создания)
    path('tag_management/', views.tag_management, name='tag_management'),
    
    #Работает
    path('tags/create', views.tag_create, name='tag_create'),
    path('tags/<int:tag_id>/edit/', views.tag_edit, name='tag_edit'),
    path('tags/<int:tag_id>/delete/', views.tag_delete, name='tag_delete'),

    #Работает
    path('teacher/course/create/', views.course_create, name='course_create'),
    path('teacher/module/create/', views.module_create, name='module_create'),
    path('teacher/lesson/create/', views.lesson_create, name='lesson_create'),
    
    #Работает
    path('teacher/course/<int:pk>/edit/', views.course_edit, name='course_edit'),
    path('teacher/course/<int:pk>/manage/', views.course_manage, name='course_manage'),
    path('teacher/course/<int:pk>/delete/', views.course_delete, name='course_delete'),

    #Работает
    path('teacher/module/<int:pk>/edit/', views.module_edit, name='module_edit'),
    path('teacher/module/<int:pk>/delete/', views.module_delete, name='module_delete'),
    path('teacher/lesson/<int:pk>/edit/', views.lesson_edit, name='lesson_edit'),
    path('teacher/lesson/<int:pk>/delete/', views.lesson_delete, name='lesson_delete'),

    #Работает
    path('student/courses', views.student_courses, name='student_courses'),
    path('student/course/<int:course_id>/', views.course_modules, name='course_modules'),
    path('student/lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),

    path('student/lesson/<int:lesson_id>/complete/', views.complete_lesson, name='complete_lesson'),
    path('student/lesson/<int:lesson_id>/uncomplete/', views.uncomplete_lesson, name='uncomplete_lesson'),
    # path('student/lesson/<int:lesson_id>/update-score/', views.update_lesson_score, name='update_lesson_score'),
    path('student/stats/', views.student_stats, name='student_stats'),  
]