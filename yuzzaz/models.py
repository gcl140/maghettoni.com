from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, verbose_name="Official Email", blank=True, null=True)
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True) #if none, call online avatar api
    telephone = models.CharField(max_length=13, unique=True, verbose_name="Telephone Number", blank=True, null=True)
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
    
    def __str__(self):
        return f"{self.username}"
