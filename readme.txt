APPLICATION WITH RANDOM ARTICLES FROM http://kopalniawiedzy.pl/
Python version: 3.5.2+

HOW TO RUN

1) Create virtual-env
2) Install requirements using: 'pip install -r requirements.txt'
3) Run 'python manage.py migrate' to create db
4) Run application using 'python manage.py runserver'
5) Run 'python manage.py my_script' to get articles data from outter website, parse it and save into db

1. Basic information
Application is developed in Python, using the Django framework. Front end is based on HTML, Bootstrap and JQuery. Database is created in SQLite. Not deployed yet.

2. Functionality
Application allows to:
- search random article from database.
- search random article using advance settings.

3. Application structure
- application is developed using MVT design pattern.
- database model is defined in arts/models.py
- views handles all the requests are defined in arts/views.py
- static files are located in arts/static
- html templates are located in arts/templates
- configuration settings are located in 10_articles/settings.py
- migrations are located in arts/migrations
- there is my_script.py in arts/management. It downloads articles  from the Internet, parses them and saves in the db. Script uses bs4 and requests libs.

4. To do:
- poll,
- postgresql,
- login/logout system, user settings, profile settings,
- more different websites to download articles from,
- deploy on heroku,
- more advance admin panel,
- tests
