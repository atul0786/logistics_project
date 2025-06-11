from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.http import HttpResponse

# 🔥 Add this test view
def trigger_error(request):
    division_by_zero = 1 / 0
    return HttpResponse("This should never return.")  # Not actually needed

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='login/'), name='redirect_to_login'),  
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
    path('dealer/', include(('dealer_app.urls', 'dealer'), namespace='dealer')),
    path('transporter/', include(('transporter_app.urls', 'transporter'), namespace='transporter')),
    path('glitchtip-debug/', trigger_error),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
