from django.conf import settings
from django.contrib import admin

from .models import Group, Post


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group'
    )
    search_fields = ('text',)
    list_filter = ('pub_date',)
    list_editable = ('group',)
    empty_value_display = settings.DISPLAY_VALUE


admin.site.register(Post, PostAdmin)
admin.site.register(Group)
