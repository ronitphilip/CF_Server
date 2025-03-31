from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class Authenticate(ModelBackend):
        
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(email=username) if "@" in username else User.objects.get(username=username)
            if user.check_password(password):
                return user
            else:
                print("Password mismatch")
                return None
        except User.DoesNotExist:
            print("User does not exist")
            return None
