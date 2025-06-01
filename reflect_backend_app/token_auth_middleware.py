from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.db import close_old_connections

class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        from django.contrib.auth.models import AnonymousUser
        from rest_framework_simplejwt.authentication import JWTAuthentication

        query_string = scope.get("query_string", b"").decode()
        token = parse_qs(query_string).get("token")

        if token:
            print(f"💬 WebSocket token received: {token[0]}")
            try:
                jwt_auth = JWTAuthentication()
                validated_token = jwt_auth.get_validated_token(token[0])

                user = await database_sync_to_async(jwt_auth.get_user)(validated_token)

                print(f"Authenticated WebSocket user: {user.username}")
                scope["user"] = user
            except Exception as e:
                print(f"JWT auth failed: {str(e)}")
                scope["user"] = AnonymousUser()
        else:
            print("No token in query string")
            scope["user"] = AnonymousUser()

        close_old_connections()
        return await super().__call__(scope, receive, send)
