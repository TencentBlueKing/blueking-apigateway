from django.core.exceptions import ImproperlyConfigured
from environ import Env as BaseEnv


class SettingsError(Exception):
    pass


class Env(BaseEnv):
    def get_value(self, *args, **kwargs):
        try:
            return super(Env, self).get_value(*args, **kwargs)
        except ImproperlyConfigured as e:
            raise SettingsError from e
