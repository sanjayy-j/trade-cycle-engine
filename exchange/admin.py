"""Django admin registrations for core exchange models."""

from django.contrib import admin

from .models import Item, User, Want

admin.site.register(User)
admin.site.register(Item)
admin.site.register(Want)
