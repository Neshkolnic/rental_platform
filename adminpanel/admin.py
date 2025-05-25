from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import ModerationAssignment, SupportAssignment

admin.site.register(ModerationAssignment)
admin.site.register(SupportAssignment)