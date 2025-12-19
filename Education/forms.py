from django import forms
from .models import *
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

class StudentRegistrationForm(forms.ModelForm):
    """Форма регистрации студента на основе модели"""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        }),
        label='Пароль',
        min_length=6
    )
    
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Повторите пароль'
        }),
        label='Подтверждение пароля'
    )
    
    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'email', 'phone', 'date_of_birth']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите ваше имя'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите вашу фамилию'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите ваш email'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+7 (XXX) XXX-XX-XX'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Пароли не совпадают')
        
        return cleaned_data
    
    def clean_email(self):
        email = self.cleaned_data['email']
        
        # Проверяем, нет ли уже пользователя с таким email
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже зарегистрирован')
        
        # Проверяем, нет ли уже студента или преподавателя с таким email
        if Student.objects.filter(email=email).exists():
            raise forms.ValidationError('Студент с таким email уже зарегистрирован')
        
        if Reviewer.objects.filter(email=email).exists():
            raise forms.ValidationError('Преподаватель с таким email уже зарегистрирован')
        
        return email
    
class ReviewerRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        }),
        label='Пароль',
        min_length=6
    )
    
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Повторите пароль'
        }),
        label='Подтверждение пароля'
    )
    
    experience_years = forms.IntegerField(
        min_value=0,
        max_value=50,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Опыт работы в годах'
        }),
        label='Опыт работы (лет)',
        required=False
    )
    
    class Meta:
        model = Reviewer
        fields = ['first_name', 'last_name', 'email', 'phone', 'specialization', 'hire_date']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите ваше имя'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите вашу фамилию'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите ваш email'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+7 (XXX) XXX-XX-XX'
            }),
            'specialization': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Python, Веб-разработка, Data Science'
            }),
            'hire_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
        labels = {
            'specialization': 'Специализация',
            'hire_date': 'Дата начала работы',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Пароли не совпадают')
        
        return cleaned_data
    
    def clean_email(self):
        email = self.cleaned_data['email']
        
        # Проверяем, нет ли уже пользователя с таким email
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже зарегистрирован')
        
        # Проверяем, нет ли уже преподавателя или студента с таким email
        if Reviewer.objects.filter(email=email).exists():
            raise forms.ValidationError('Преподаватель с таким email уже зарегистрирован')
        
        if Student.objects.filter(email=email).exists():
            raise forms.ValidationError('Студент с таким email уже зарегистрирован')
        
        return email


class CustomAuthenticationForm(AuthenticationForm):
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username is not None and password:
            # Проверяем, существует ли пользователь
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                raise forms.ValidationError('Пользователь с таким email не найден')
            
            # Аутентифицируем пользователя
            self.user_cache = authenticate(self.request, username=username, password=password)
            
            if self.user_cache is None:
                raise forms.ValidationError('Неверный пароль')
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data
    

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name', 'description', 'slug', 'color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название тега'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Описание тега (необязательно)'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите url тега'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'style': 'height: 40px;'
            }),
        }
        labels = {
            'name': 'Название тега',
            'description': 'Описание',
            'color': 'Цвет тега',
        }


class CourseTagForm(forms.ModelForm):
    tag = forms.ModelChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Выберите тег'
    )
    
    class Meta:
        model = CourseTag
        fields = ['tag']


class CourseForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Теги'
    )
    
    class Meta:
        model = Course
        fields = [
            'title', 'description', 'price', 'duration_weeks', 
            'difficulty_level', 'is_active', 'complexity_level', 'tags'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'difficulty_level': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'title': 'Название курса',
            'description': 'Описание курса',
            'price': 'Цена (руб)',
            'duration_weeks': 'Длительность (недель)',
            'difficulty_level': 'Уровень сложности',
            'complexity_level': 'Уровень сложность от 1 до 5',
            'is_active': 'Опубликовать курс',
        }

class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['course', 'title', 'description', 'module_order']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'module_order': forms.NumberInput(attrs={'min': 1}),
        }
        labels = {
            'course': 'Курс',
            'title': 'Название модуля',
            'description': 'Описание модуля',
            'module_order': 'Порядковый номер',
        }

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = [
            'module', 'title', 'content', 'lesson_type', 'duration_minutes', 
            'lesson_order', 'video_url', 'max_score',
            'is_active', 'is_required'
        ]
        widgets = {
            'module': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={'rows': 6}),
            'lesson_type': forms.Select(attrs={'class': 'form-select'}),
            'lesson_order': forms.NumberInput(attrs={'min': 1}),
            'max_score': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'video_url': forms.URLInput(attrs={'placeholder': 'https://...'}),
        }
        labels = {
            'module': 'Модуль',
            'title': 'Название урока',
            'content': 'Содержание урока',
            'lesson_order': 'Порядковый номер в модуле',
            'video_url': 'Видео URL',
            'is_active': 'Активный урок',
            'is_free': 'Необходимый урок',
        }
    

class CourseSearchForm(forms.Form):
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по названию курса...',
            'aria-label': 'Search'
        }),
        label=''
    )
    
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'data-placeholder': 'Выберите теги...'
        }),
        label='Теги'
    )
    
    difficulty = forms.ChoiceField(
        choices=[('', 'Любой уровень')] + list(DifficultyLevel.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Уровень сложности'
    )

class TagFilterForm(forms.Form):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.filter(is_featured=True),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label='Популярные теги'
    )


