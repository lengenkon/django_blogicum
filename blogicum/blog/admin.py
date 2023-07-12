from django.contrib import admin
from .models import Category, Post, Location


class PostAdmin(admin.ModelAdmin):
    date_hierarchy = "pub_date"
    empty_value_display = "-Нет-"
    list_display = (
        'title',
        'pub_date',
        'author',
        'location',
        'category',
        'is_published',
    )
    list_editable = (
        'is_published',
        'category',
        'location',
    )
    search_fields = ('title',)
    list_filter = ('category', 'location', 'author')
    list_display_links = ('title',)


class PostInline(admin.TabularInline):
    model = Post
    extra = 0


class CategoryAdmin(admin.ModelAdmin):
    inlines = (PostInline,)
    list_display = ('title',)


class LocationAdmin(admin.ModelAdmin):
    inlines = (PostInline,)
    list_display = ('name',)


admin.site.register(Category, CategoryAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Location, LocationAdmin)
