from django.db import models
from django.core.validators import RegexValidator 
from django.utils.translation import gettext_lazy as _

#Auxiliares para estructura
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
class Publisher(TimeStampedModel):
    name = models.CharField(max_lenght=255)
    place = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return self.name

class Subject(TimeStampedModel):
    term = models.CharField(max_length=255, unique=True)
    
    def __str__(self):
        return self.term
    
class Location(TimeStampedModel):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
class Person(TimeStampedModel):
    given = models.CharField(_("Nombres"), max_length=255, blank=True)
    family = models.CharField(_("Apellidos"), max_length=255, blank=True)
    full_name = models.CharField(max_length=255, unique=True)
    