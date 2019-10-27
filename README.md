# Udactiy Catalog App

## Project Overview

this is an application that provides a list of items within a variety of categories as well as provide a user registration and authentication system. Registered users will have the ability to post, edit and delete their own items.

## Requirements

to lunch the application you must install :

* Python 3, to check version: Python --version
* Vagrant
* Virtual Box
* Oauth Cient

you need also the following dependencies:

* requests
* Flask
* oauthlib

to install them just run in your terminal the following command `pip  install  -r  requirements.txt`

## How to run

please follow these steps to run the application :

* Start Terminal and navigate to the project folder, cd to the vagrant directory.
* Launch the Vagrant VM inside Vagrant sub-directory: using command: vagrant up and log in command vagrant ssh
* Run `python database_setup.py` to create sqlite database and tables.
* To populate the database run `python init_db_rows.py`
* Run `python project.py` to run the application, after that connect to the localhost:8000.

if you want to add,edit and delete items, you must have a google account and login with it in the application.
