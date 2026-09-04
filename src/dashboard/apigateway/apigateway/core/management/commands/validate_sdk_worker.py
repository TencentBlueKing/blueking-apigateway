import json

from django.core.management.base import BaseCommand, CommandError

from apigateway.biz.sdk.exceptions import SDKConfigurationError
from apigateway.biz.sdk.toolchain import validate_sdk_worker_environment


class Command(BaseCommand):
    help = "Validate the SDK generation worker configuration and toolchain"
    requires_system_checks: list[str] = []

    def handle(self, *args, **options):
        try:
            identity = validate_sdk_worker_environment()
        except SDKConfigurationError as error:
            raise CommandError(str(error)) from error
        self.stdout.write(json.dumps(identity, sort_keys=True))
