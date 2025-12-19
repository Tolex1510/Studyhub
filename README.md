# StudyHub - система курсов для обучения

Проект StudyHub позволяет создавать курсы от лица преподавателей и обучаться курсами преподавателямм

## Features

* Простая и быстрая регистрация
* Возможность создания любых курсов
* Поиск курсов по тегу и названию
* Прогрессия обучения студента

## Tech Stack

* **Бекенд** - Python, Django
* **Database** - PostgreSQL
* **Фронтенд** - Django Templates (HTML, CSS, JS)

## Installation

Для установки проекта, создания виртуального окружения и установки необходимых пакетов нужно:
```bash
git clone https://github.com/Tolex1510/Studyhub.git
cd Studyhub
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Также для создания бд нужно использовать команду:

```bash
python manage.py migrate
```

Для запуска проекта нужно использовать команду:
```bash
python manage.py runserver
```

## Screenshots

![](Home.png)

![](Courses.png)

![](Tags.png)

![](Teacher_Dashboard.png)

## ER-диаграмма

![](Database.png)

## Архитектурная схема

```mermaid
graph TB
    subgraph "Клиентская часть"
        BROWSER[Браузер пользователя]
    end

    subgraph "Серверная часть Django"
        SERVER[Django сервер]
        
        subgraph "Основные компоненты"
            URLS[URL маршрутизация]
            VIEWS[Views обработчики]
            MODELS[Models ORM]
            TEMPLATES[HTML шаблоны]
            FORMS[Формы валидация]
        end
    end

    subgraph "База данных PostgreSQL"
        DB[(PostgreSQL<br/>Таблицы:<br/>- Пользователи<br/>- Курсы<br/>- Модули<br/>- Уроки<br/>- Прогресс)]
    end

    %% Основные связи
    BROWSER -- "HTTP/HTTPS запросы" --> SERVER
    SERVER --> URLS
    URLS --> VIEWS
    VIEWS --> MODELS
    VIEWS --> TEMPLATES
    VIEWS --> FORMS
    MODELS -- "ORM запросы" --> DB

    
    TEMPLATES -- "HTML/CSS/JS" --> BROWSER

    classDef client fill:#e1f5fe,stroke:#01579b
    classDef server fill:#f3e5f5,stroke:#4a148c
    classDef db fill:#e8f5e8,stroke:#1b5e20
    
    class BROWSER client
    class SERVER,URLS,VIEWS,MODELS,TEMPLATES,FORMS server
    class DB db
```