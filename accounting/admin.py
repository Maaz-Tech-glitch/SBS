from django.contrib import admin
from .models import Account, JournalEntry

admin.site.register(Account)
admin.site.register(JournalEntry)