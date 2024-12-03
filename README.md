# Foodgram
![badge](https://github.com/Andrew25Egorov/foodgram/actions/workflows/main.yml/badge.svg)

## Описание проекта:
«Foodgram» (Продуктовый помощник) — это сайт для размещения различных кулинарных рецептов, на котором зарегистрированные пользователи могут создавать (корректировать/удалять) и публиковать свои интересные рецепты, добавлять любые рецепты в избранное и подписываться на других авторов. Пользователям сайта также  доступен сервис «Список покупок». Он позволяет создать список продуктов с количеством, которые нужно купить для приготовления выбранных на сайте блюд. Для удобства навигации по сайту при просмотре рецептов, они могут быть отфильтрованы по различным тэгами. Для неавторизированных пользователей доступны просмотр рецептов и страниц авторов.

![](https://pictures.s3.yandex.net/resources/image_1711954469.png)


## СТЕК технологий:

![image](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue)
![image](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
![image](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green)
![image](https://img.shields.io/badge/django%20rest-ff1709?style=for-the-badge&logo=django&logoColor=white)
![image](https://img.shields.io/badge/VSCode-0078D4?style=for-the-badge&logo=visual%20studio%20code&logoColor=white)
![image](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)
![Git](https://img.shields.io/badge/git-%23F05033.svg?style=for-the-badge&logo=git&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![image](https://img.shields.io/badge/DockerHub-1488C6?style=for-the-badge&logo=docker&logoColor=white)
![image](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![image](https://img.shields.io/badge/Ubuntu-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)
![image](https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white)
![image](https://img.shields.io/badge/Gunicorn-00A98F?style=for-the-badge&logo=gunicorn&logoColor=white)
![GitHubActions](https://img.shields.io/badge/github%20actions-%232671E5.svg?style=for-the-badge&logo=githubactions&logoColor=white)


* Python == 3.9.13
* Django == 3.2.3
* Django Rest Framework == 3.12.4
* Gunicorn == 20.1.0
* Nginx
* Docker
* PostgreSQL

## Работа по проекту:

**Поставленная задача — написать бэкенд в виде REST API для веб-приложения «Фудграм», а также опубликовать это веб-приложение на виртуальном удалённом сервере.**

**Этапы работы по проекту:**

1. Создание Restful API.
2. Запуск проекта в контейнерах.
3. Подключение СУБД PostgreSQL.
4. Создание volumes для сохранения загруженной информации.
5. Получение доменного имени и SSL-сертификата для безопасного протокола передачи данных.
6. Деплой на сервер с настройкой nginx и Gunicorn.
7. Непрерывная CI/CD посредством GitHub Actions.

 ### Смотреть развернутый проект    <https://andrewegorov.ru/>


## Настройка автоматизации деплоя: CI/CD

1. Файл workflow находится в директории

    ```bash
    foodgram/.github/workflows/main.yml
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
git clone git@github.com:Andrew25Egorov/foodgram.git
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
