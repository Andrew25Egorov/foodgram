# Foodgram
![badge](https://github.com/Andrew25Egorov/kittygram_final/actions/workflows/main.yml/badge.svg)

## Описание проекта:
Kittygram — социальная сеть для любителей котов и котиков.
Это рабочий сервис, который состоит из бэкенд-приложения на Django и фронтенд-приложения на React.
Проект позволяет:
- Добавлять, просматривать, редактировать и удалять фотографии своих котов.
- Добавлять новые и присваивать уже существующие достижения. 
- Просматривать чужих котов и их достижения.

## СТЕК технологий:





![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white) ![DjangoREST](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray) ![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white) ![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white) ![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=for-the-badge&logo=nginx&logoColor=white) ![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E) ![React](https://img.shields.io/badge/react%20-%2320232a.svg?&style=for-the-badge&logo=react&logoColor=%2361DAFB)  ![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white) ![GitHubActions](https://img.shields.io/badge/github%20actions-%232671E5.svg?style=for-the-badge&logo=githubactions&logoColor=white)

* Python == 3.9.13
* Django == 3.2.3
* Django Rest Framework == 3.12.4
* Gunicorn == 20.1.0
* Nginx
* Docker
* PostgreSQL

## Работа по проекту:

-  Получено доменное имя
-  На удаленный сервер был установлен Git, Docker
-  Был связан аккаунт на GitHub и на DockerHub с удаленным сервером
-  Были созданы образы для бэкенд, фронтенд приложений
-  Настроена совместная работа контейнеров бэкэнда и базы данных
-  Настроен веб-сервер Nginx для перенаправления запросов и работы со статикой проекта
-  Подключено шифрование запросов по протоколу HTTPS
-  Автоматизировано тестирование и деплой проекта Kittygram с помощью GitHub Actions
 ### Смотреть развернутый проект    <https://andrewegorov.ru/>


## Настройка автоматизации деплоя: CI/CD

1. Файл workflow находится в директории

    ```bash
    kittygram/.github/workflows/main.yml
    ```

2. Для адаптации его на своем сервере добавьте секреты в GitHub Actions:

    ```bash
    DOCKER_USERNAME                # имя пользователя в DockerHub
    DOCKER_PASSWORD                # пароль пользователя в DockerHub
    HOST                           # ip_address сервера
    USER                           # имя пользователя
    SSH_KEY                        # приватный ssh-ключ
    SSH_PASSPHRASE                 # кодовая фраза (пароль) для ssh-ключа

    TELEGRAM_TO                    # id телеграм-аккаунта (можно узнать у @userinfobot, команда /start)
    TELEGRAM_TOKEN                 # токен бота (получить токен можно у @BotFather, /token, имя бота)
    ```
3. Автоматизация настроена с помощью сервиса GitHub Actions.

**При push в ветку "main":**
* проект тестируется;
* в случае успешного прохождения тестов, образы обновляются на Docker Hub;
* на сервере запускаются контейнеры из обновлённых образов;
* после успешного деплоя вам приходит сообщение в Телеграм.


## Запуск проекта из исходников GitHub

1. Клонируйте себе репозиторий: 

```bash 
git clone git@github.com:Andrew25Egorov/kittygram.git
```

2. Выполните запуск:

```bash
sudo docker compose -f docker-compose.yml up
```

3. После запуска необходимо выполнить сбор статики и миграции бэкенда. Статика фронтенда собирается во время запуска контейнера, после чего он останавливается. 

```bash
sudo docker compose -f docker-compose.yml exec backend python manage.py migrate

sudo docker compose -f docker-compose.yml exec backend python manage.py collectstatic

sudo docker compose -f docker-compose.yml exec backend cp -r /app/collected_static/. /static/static/
```

4. Проект доступен на: 

```
http://localhost:8000/
```



## Автор backend 
студент 89 когорты
Андрей Егоров