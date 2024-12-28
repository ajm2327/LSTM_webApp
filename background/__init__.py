from .tasks import BackgroundTaskManager
from .config import BackgroundConfig

def init_background_tasks(app):
    return BackgroundTaskManager(app)