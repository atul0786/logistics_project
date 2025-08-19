from pathlib import Path
import os
from dotenv import load_dotenv
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="https://22a98797a6824447b9ec83b52f06fcda@app.glitchtip.com/11692",
    integrations=[DjangoIntegration()],
    auto_session_tracking=False,
    traces_sample_rate=0.01,  # 1% performance tracing
    send_default_pii=True,    # To capture user data
    release="1.0.0",
    environment="production",
)

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-default-key')
DEBUG = False
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '147.93.110.231,localhost,127.0.0.1,tphg1.clk800.online').split(',')

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# Installed apps
INSTALLED_APPS = [
    'django.contrib.admin',
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
    'corsheaders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
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
        'DIRS': [BASE_DIR / 'logistics_project' / 'templates', BASE_DIR / 'templates'],
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

# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'good_way_express'),
        'USER': os.getenv('DB_USER', 'good_way_express_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', '0786'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Authentication settings
AUTH_USER_MODEL = 'dealer_app.CustomUser'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = '/dealer/create_cnote/'
LOGOUT_REDIRECT_URL = 'login'

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'logistics_project', 'static'),
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_NAME = 'sessionid'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# CORS settings (restrict in production)
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost,http://127.0.0.1').split(',')
CORS_ALLOW_CREDENTIALS = True

# ✅ WORKING BETTER STACK CONFIGURATION
BETTER_STACK_TOKEN = os.getenv('BETTER_STACK_TOKEN', 'pXbKbfxiZqDH2PWp3JWP2VZF')
BETTER_STACK_HOST = 's1369340.eu-nbg-2.betterstackdata.com'

# Create logs directory
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# Custom HTTP Handler for Better Stack
import logging
import json
import urllib.request
import urllib.parse
from datetime import datetime

class BetterStackHTTPHandler(logging.Handler):
    """Custom HTTP handler for Better Stack logging"""
    
    def __init__(self, host, token):
        super().__init__()
        self.host = host
        self.token = token
        self.url = f'https://{host}'
    
    def emit(self, record):
        try:
            # Format log message
            log_entry = {
                'dt': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
                'level': record.levelname,
                'module': record.module,
                'message': self.format(record),
                'source': 'django_good_way_express'
            }
            
            # Prepare request
            data = json.dumps(log_entry).encode('utf-8')
            req = urllib.request.Request(
                self.url,
                data=data,
                headers={
                    'Authorization': f'Bearer {self.token}',
                    'Content-Type': 'application/json',
                    'User-Agent': 'Django-GoodWayExpress/1.0'
                },
                method='POST'
            )
            
            # Send request (non-blocking)
            urllib.request.urlopen(req, timeout=5)
            
        except Exception as e:
            # Don't let logging errors crash the app
            pass

# ✅ COMPLETE DUAL LOGGING CONFIGURATION
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
        'better_stack_format': {
            'format': 'GoodWayExpress: {levelname} {module} - {message}',
            'style': '{',
        },
    },
    'handlers': {
        # Console handler - Terminal mein dikhega
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': 'INFO',
        },
        
        # File handler - Local file mein save hoga (WORKING)
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'app.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
            'level': 'INFO',
        },
        
        # ✅ Better Stack HTTP handler - Working configuration
        'better_stack': {
            '()': BetterStackHTTPHandler,
            'host': BETTER_STACK_HOST,
            'token': BETTER_STACK_TOKEN,
            'formatter': 'better_stack_format',
            'level': 'INFO',
        },
        
        # Null handler - Backup
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    
    # Root logger
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    
    'loggers': {
        # Django framework logs
        'django': {
            'handlers': ['console', 'file', 'better_stack'],
            'level': 'INFO',
            'propagate': False,
        },
        
        # Django request logs (404, 500 errors etc)
        'django.request': {
            'handlers': ['console', 'file', 'better_stack'],
            'level': 'WARNING',
            'propagate': False,
        },
        
        # Django security logs
        'django.security': {
            'handlers': ['console', 'file', 'better_stack'],
            'level': 'WARNING',
            'propagate': False,
        },
        
        # Dealer app logs
        'dealer_app': {
            'handlers': ['console', 'file', 'better_stack'],
            'level': 'INFO',
            'propagate': False,
        },
        
        # Transporter app logs
        'transporter_app': {
            'handlers': ['console', 'file', 'better_stack'],
            'level': 'INFO',
            'propagate': False,
        },
        
        # Logistics project logs
        'logistics_project': {
            'handlers': ['console', 'file', 'better_stack'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Crispy Forms Configuration
CRISPY_TEMPLATE_PACK = 'bootstrap4'

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
}

print("✅ Good Way Express - Complete Dual Logging Configuration Loaded!")
print(f"📁 Local logs: {LOGS_DIR / 'app.log'}")
print(f"🌐 Better Stack: {BETTER_STACK_HOST}")
print("🚀 Ready for production!")
