from django.contrib import admin

# Register your models here.
from core.models import Item, Author, Genre, ItemInstance, User, Situation, Borrowing


class ItemAdmin(admin.ModelAdmin):
    """
    Admin object for Item model :
    """
    list_display = ('title', 'get_instance_count')

admin.site.register(Item, ItemAdmin)
admin.site.register(Author)
admin.site.register(Genre)
admin.site.register(ItemInstance)
admin.site.register(User)
admin.site.register(Situation)
admin.site.register(Borrowing)
