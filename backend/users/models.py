from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(
        verbose_name='email',
        unique=True
    )
    username = models.CharField(
        max_length=50,
        verbose_name='username',
        unique=True,
        db_index=True
    )
    first_name = models.CharField(
        max_length=50,
        verbose_name='name'
    )
    last_name = models.CharField(
        max_length=50,
        verbose_name='surname'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Users'
        verbose_name_plural = 'Users'
        ordering = ('id',)

    def __str__(self):
        return self.username
