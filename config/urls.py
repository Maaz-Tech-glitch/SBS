# from django.conf import settings
# from django.conf.urls.static import static
# from django.contrib import admin
# from django.urls import include, path

# urlpatterns = [
#     path("admin/", admin.site.urls),
#     path("api/users/", include("users.urls")),
#     path("api/", include("products.urls")),
#     path("api/billing/", include("billing.urls")),
#     path("api/dashboard/", include("dashboard.urls")),
#     path("api/reports/", include("reports.urls")),
# ]

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("users.urls")),      # <-- Update: 'api/users/' ki jagah 'api/' kar diya
    path("api/", include("products.urls")),
    path("api/billing/", include("billing.urls")),
    path("api/dashboard/", include("dashboard.urls")),
    path("api/reports/", include("reports.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)