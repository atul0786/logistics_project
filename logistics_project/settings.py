from pathlib import Path  
import os  
  
LOGIN_URL = 'login'  
LOGIN_REDIRECT_URL = '/dealer/create_cnote/'  # Adjust this path to match your CNote creation URL  
  
LOGOUT_REDIRECT_URL = 'login'  
  
BASE_DIR = Path(__file__).resolve().parent  # Now pointing to 'logistics'  
  
SECRET_KEY = 'django-insecure-@jcjdu2*cprnhxp1eim1c4td1p3ef55-v6wksl1*t&$a-da14)'  
  
DEBUG = True  
  
ALLOWED_HOSTS = []  
  
INSTALLED_APPS = [  'django.contrib.admin',
                  'django.contrib.auth',  
                  'django.contrib.contenttypes',  
                  'django.contrib.sessions',  
                  'django.contrib.messages',  
                  'django.contrib.staticfiles',  
                  'dealer_app',  
                  'transporter_app',  
                  'crispy_forms',  
                  'crispy_bootstrap4',
                  'django_extensions',  
                  'rest_framework',

]  
  
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap4"  
CRISPY_TEMPLATE_PACK = 'bootstrap4'  
  
MIDDLEWARE = [  
    'django.middleware.security.SecurityMiddleware',  
    'django.contrib.sessions.middleware.SessionMiddleware',  
    'django.middleware.common.CommonMiddleware',  
    'django.middleware.csrf.CsrfViewMiddleware',  
    'django.contrib.auth.middleware.AuthenticationMiddleware',  
    'django.contrib.messages.middleware.MessageMiddleware',  
    'django.middleware.clickjacking.XFrameOptionsMiddleware',  
]  
  
ROOT_URLCONF = 'logistics_project.urls'  
  
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]  
WSGI_APPLICATION = 'logistics_project.wsgi.application'  
  
DATABASES = {  
'default': {  
'ENGINE': 'django.db.backends.postgresql',  
'NAME': 'good_way_express',  
'USER': 'user1',  
'PASSWORD': '0786',  
'HOST': 'localhost',  
'PORT': '5433',  
}  
}  
  
AUTH_PASSWORD_VALIDATORS = [  
{  
    'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',  
    },  
    {  
          'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',  
          },  
          {
              'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',  
              },  
              {  
                  'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',  
                  },  
]  
  
LANGUAGE_CODE = 'en-us'  
  
TIME_ZONE = 'UTC'  
  
USE_I18N = True  
  
USE_TZ = True  
  
STATIC_URL = '/static/'  
  
STATICFILES_DIRS = [  
    BASE_DIR / 'static',  
]  
  
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  
  
AUTH_USER_MODEL = 'dealer_app.CustomUser'  
  
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'  
  
MEDIA_URL = '/media/'  
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  
  
LOGGING = {  
    'version': 1,  
    'disable_existing_loggers': False,  
    'handlers': {  
        'console': {  
            'class': 'logging.StreamHandler',  
            },  
            },  
            'root': {  
                'handlers': ['console'],  
                'level': 'INFO',  
                },  
                'loggers': {  
                    'django': {  
                        'handlers': ['console'],  
                        'level': 'INFO',  
                        'propagate': False,  
                        },  
                        },  
}
