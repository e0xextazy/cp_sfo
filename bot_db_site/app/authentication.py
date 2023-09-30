from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import status
from rest_framework.authtoken.models import Token

class CustomTokenAuthentication(TokenAuthentication):
    def authenticate_credentials(self, key):
        try:
            token = Token.objects.get(key=key)
        except Token.DoesNotExist:
            raise AuthenticationFailed("Invalid token", code=status.HTTP_401_UNAUTHORIZED)

        user = token.user

        if not user.is_active:
            raise AuthenticationFailed("User is not active", code=status.HTTP_401_UNAUTHORIZED)

        return (user, token)
