from djoser.views import UserViewSet as BaseUserViewSet

from users import models as user_models

from .serializers import UserSerializers


class UserViewSet(BaseUserViewSet):
    queryset = user_models.User.objects.all()
    serializer_class = UserSerializers
