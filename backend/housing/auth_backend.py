from django.contrib.auth.backends import ModelBackend
from django.core.cache import cache
from django.contrib.auth import get_user_model

class CachedModelBackend(ModelBackend):
    """
    Ultra-fast cached auth backend that caches authenticated User, UserProfile,
    and Student in memory (LocMemCache) to eliminate transatlantic SQL round trips on every request.
    """
    def get_user(self, user_id):
        cache_key = f"cached_auth_user_{user_id}"
        user = cache.get(cache_key)
        if user is None:
            UserModel = get_user_model()
            try:
                user = (
                    UserModel._default_manager
                    .select_related('profile__student_profile')
                    .get(pk=user_id)
                )
                cache.set(cache_key, user, 1800)
            except UserModel.DoesNotExist:
                return None
        return user
