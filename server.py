import sys
# Block typer from intercepting
sys.modules['typer'] = None

import gunicorn.app.base
from app.main import app

class StandaloneApplication(gunicorn.app.base.BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

if __name__ == '__main__':
    options = {
        'bind': '127.0.0.1:8000',
        'workers': 1,
        'worker_class': 'uvicorn.workers.UvicornWorker',
    }
    StandaloneApplication(app, options).run()
