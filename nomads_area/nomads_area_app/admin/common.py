from django.contrib import admin


admin.site.site_header = "Nomads Area Admin"
admin.site.site_title = "Nomads Area"
admin.site.index_title = "Панель"


class TranslationMediaMixin:
    class Media:
        js = ("https://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js",
              "https://ajax.googleapis.com/ajax/libs/jqueryui/1.10.2/jquery-ui.min.js",
              "modeltranslation/js/tabbed_translation_fields.js")
        css = {"screen": ("modeltranslation/css/tabbed_translation_fields.css",)}
