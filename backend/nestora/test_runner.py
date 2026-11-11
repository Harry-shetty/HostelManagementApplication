"""Custom test runner so `manage.py test` discovers apps inside `backend/`."""

from django.conf import settings
from django.test.runner import DiscoverRunner


class BackendDiscoverRunner(DiscoverRunner):
    """Discover tests inside `BACKEND_DIR` when no test labels are supplied."""

    def build_suite(self, test_labels=None, **kwargs):
        if not test_labels:
            test_labels = [str(settings.BACKEND_DIR)]
        return super().build_suite(test_labels, **kwargs)
