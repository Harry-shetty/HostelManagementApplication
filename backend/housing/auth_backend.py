from django.contrib.auth.backends import ModelBackend
from django.core.cache import cache
from django.contrib.auth import get_user_model

class CachedModelBackend(ModelBackend):
    """
    Ultra-fast cached auth backend that caches authenticated User and UserProfile
    in memory (LocMemCache) to eliminate transatlantic SQL round trips on every request.
    """
    def get_user(self, user_id):
        cache_key = f"cached_auth_user_{user_id}"
        user = cache.get(cache_key)
        if user is None:
            user = super().get_user(user_id)
            if user:
                # Pre-fetch profile and student_profile so decorators/views don't fire extra queries
                try:
                    profile = getattr(user, 'profile', None)
                    if profile:
                        _ = getattr(profile, 'student_profile', None)
                except Exception:
                    pass
                cache.set(cache_key, user, 300)
        return user
