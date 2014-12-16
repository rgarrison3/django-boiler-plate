# django
from django.db import models
from django.contrib.auth.models import UserManager
from django.contrib.auth import get_user_model

class UserManager(UserManager, NoCountManager):
    '''
    Custom manager to implement our custom create_user
    and create_superuser methods.
    '''

    def create_user(self, username, password=None, **extra_fields):
        '''
        Creates and saves a Person with the given username.
        '''
        if not username:
            raise ValueError('A valid username is required.')

        user = get_user_model()(username=username, **extra_fields)
        if password is not None:
            user.set_password(password)

        # The person has not logged in
        user.last_login = None
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password, **extra_fields):
        '''
        Creates and saves a superuser Person.
        '''
        if password is None:
            raise Exception("Must supply a password for new superusers.")

        user = self.create_user(username, password, **extra_fields)
        user.is_staff = True
        user.is_active = True
        user.is_superuser = True
        user.save(using=self._db)
        return user
