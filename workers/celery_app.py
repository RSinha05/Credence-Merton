import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from celery import Celery
from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

celery_app = Celery('credence_mertonx')

celery_app.conf.update(
    broker_url=CELERY_BROKER_URL,
    result_backend=CELERY_RESULT_BACKEND,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    task_track_started=True,
    result_expires=3600,
    imports=['workers.tasks']
)
