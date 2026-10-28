from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # ── Redirect allauth default pages to our custom pages ──
    path('accounts/login/',  RedirectView.as_view(url='/login/',  permanent=False)),
    path('accounts/signup/', RedirectView.as_view(url='/login/',  permanent=False)),
    path('accounts/logout/', RedirectView.as_view(url='/logout/', permanent=False)),

    # Admin
    path('admin/', admin.site.urls),

    # Auth
    path('', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),

    # Apps
    path('chat/',          include('chat.urls')),
    path('meetings/',      include('meetings.urls')),
    path('tasks/',         include('tasks.urls')),
    path('files/',         include('files.urls')),
    path('ai/',            include('ai.urls')),
    path('payments/',      include('payments.urls')),
    path('whiteboard/',    include('whiteboard.urls')),
    path('owner/',         include('owner.urls')),
    path('notifications/', include('notifications.urls')),
    path('jobs/',          include('jobs.urls')),

    # REST API - Mobile app
    path('api/v1/', include('accounts.api_urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error pages
handler404 = 'accounts.views.handler404'