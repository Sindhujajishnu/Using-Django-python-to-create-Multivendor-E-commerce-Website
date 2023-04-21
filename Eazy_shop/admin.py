from django.contrib import admin
from .models import *
# Register your models here.


class CategoryAdmin(admin.ModelAdmin):
  list_display = ('name','description','status')
admin.site.register(Catagory,CategoryAdmin)

class ProductAdmin(admin.ModelAdmin):
  list_display = ('name', 'vendor','original_price','selling_price', 'description')
admin.site.register(Product,ProductAdmin)


class VendorAdmin(admin.ModelAdmin):
  list_display = ('name', 'address','contact','status')
admin.site.register(Vendor,VendorAdmin)

