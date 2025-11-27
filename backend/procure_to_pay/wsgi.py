import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'procure_to_pay.settings')
application = get_wsgi_application()