# praktikum_new_diplom
![foodgram-project-react workflow](https://github.com/v-sinitsin/foodgram-project-react/actions/workflows/foodgram-workflow.yml/badge.svg)

### Продуктовый помощник Foodgram
Демонстрационная версия развернута на <http://62.84.118.128/>  
Учетная запись администратора для теста:
- Email: admin@admin.ru
- Пароль: admin

### Описание
Сайт для публикации рецептов

### Как запустить
1. Установите [Docker](https://www.docker.com/) для вашей ОС
2. Склонируйте [данный репозиторий](https://github.com/v-sinitsin/foodgram-project-react.git)
3. В каталоге ```infra``` создайте файл ```.env``` со следующим содержимым:
```` 
POSTGRES_DB=foodgram # имя базы данных
POSTGRES_USER=postgres # логин для подключения к БД
POSTGRES_PASSWORD=postgres # пароль для подключения к БД
DB_HOST=db # название сервиса (контейнера) с PostgreSQL
DB_PORT=5432 # порт для подключения к БД
DJANGO_SECRET_KEY=django-insecure-*%+770@+$i_4fw@^6a803gbysp&n&)h02(7!0ghoel)i*e6jlt # секретный ключ Django
````
3. В каталоге ```infra``` выполните команды для запуска всех контейнеров, применения миграций, создания суперпользователя:  
```` 
docker-compose up -d 
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic
docker-compose exec web python manage.py createsuperuser
````
### Технологии
Python  
Django  
DRF  
Docker  
Github Actions  
### Автор
[Владимир Синицин](https://github.com/v-sinitsin)