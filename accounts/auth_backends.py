from typing import Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

UserModel = get_user_model()


class UsernameOrEmailBackend(ModelBackend):
    def authenticate(
        self, request, identifier: Optional[str] = None, password: Optional[str] = None, **kwargs
    ):
        if identifier is None or password is None:
            return None
        try:
            user = UserModel.objects.get(
                Q(username__iexact=identifier) | Q(email__iexact=identifier)
            )
        except UserModel.DoesNotExist:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
