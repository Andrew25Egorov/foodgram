from rest_framework import serializers

from users import models as user_models


class UserSerializers(serializers.ModelSerializer):
    class Meta:
        model = user_models.User
        fields = (
            'id',
            'email',
            'username',
            'avatar',
            'first_name',
            'last_name',
        )
        read_only_fields = ('id',)
