# Gestion d'une médiathèque
Une application web pour gérer une base de donnée MySQL. Elle simule une plateforme pour la gestion d'une médiathèque.
## Description
Le dossier contient les fichiers de l'application web et des fichiers pour la création de la base de donnée.
## Installation
* Cloner le dossier sur votre appareil
* Créer un nouveau schnéma qur MySQL Workbench en le nommant ```librarydb```
* Executer ces commandes dans un terminal mysql
```
CREATE USER 'library_user'@'localhost' 
IDENTIFIED WITH mysql_native_password BY 'password';
GRANT ALL PRIVILEGES ON librarydb.* TO 'library_user'@'localhost';
```
Cela permet de créer un nouvel utilisateur.

* Dans le fichier racine (où se trouve ```requirement.txt```) executer cette commande : ```pip install -r requirements.txt```. Cela permet d'installer tous les packages et dépendances utilisés.
* Executer les commandes suivantes:
  * ```python manage.py makemigrations```
  * ```python manage.py migrate```
  * ```python manage.py loaddata data_fixture.json```
  * ```python manage.py runserver```
 * Se connecter au serveur ```http://127.0.0.1:8000/```
 
 Il est possible de simuler une date différente en changeant manuellement la date sous windows. Attention : Ne pas revenir en arrière dans le temps et ne pas aller trop loin en avant dans le temps, cela peut causer des problèmes avec la bdd. 
