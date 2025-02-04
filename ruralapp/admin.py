from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export import fields
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Salad, OtherDish, SideDish, WeeklyMenu, Order, WhatsAppGroup, EventLog, GroupNotification, AppState, UserProfile


class SaladAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']

class OtherDishAdmin(admin.ModelAdmin):
    list_display = ['name', 'plus_side']

class SideDishAdmin(admin.ModelAdmin):
    list_display = ['name']

class WeeklyMenuAdmin(admin.ModelAdmin):
    list_display = ['week', 'day', 'main_dish_1', 'main_dish_2', 'dessert']
    list_filter = ['day', 'week']

class OrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'order_date', 'main_dish', 'salad', 'other_dish', 'side_dish']
    list_filter = ['user', 'order_date']

class WhatsAppGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'group_id', 'phone_number']
    list_filter = ['name']

class EventLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'event_type', 'description']
    list_filter = ['timestamp', 'event_type']

class GroupNotificationAdmin(admin.ModelAdmin):
    list_display = ['group', 'message', 'send_date', 'status', 'notification_type']
    list_filter = ['group', 'send_date', 'status', 'notification_type']

class AppStateAdmin(admin.ModelAdmin):
    list_display = ['id', 'current_week']


# Define un inline para mostrar UserProfile en el panel de User
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil de usuario'

# Define una clase de administración personalizada
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline, )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'menu_status')  # Agrega 'menu_status'

    def menu_status(self, obj):
        return obj.userprofile.menu
    menu_status.boolean = True  # Muestra como un ícono de True/False
    menu_status.short_description = 'Menu Habilitado'  # Nombre de la columna

# Re-registra el modelo User
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Salad, SaladAdmin)
admin.site.register(OtherDish, OtherDishAdmin)
admin.site.register(SideDish, SideDishAdmin)
admin.site.register(WeeklyMenu, WeeklyMenuAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(WhatsAppGroup, WhatsAppGroupAdmin)
admin.site.register(EventLog, EventLogAdmin)
admin.site.register(GroupNotification, GroupNotificationAdmin)
admin.site.register(AppState, AppStateAdmin)
