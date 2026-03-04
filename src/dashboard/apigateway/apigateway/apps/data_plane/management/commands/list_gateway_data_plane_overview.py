from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count

from apigateway.core.models import Gateway


class Command(BaseCommand):
    help = "List gateway names grouped by bound data plane counts"

    def add_arguments(self, parser):
        parser.add_argument(
            "--data-plane-count",
            type=int,
            choices=[0, 1, 2, 3],
            required=False,
            help="Only display one bucket: 0/1/2/3 where 3 means 3+",
        )

    def _bucket_name(self, count: int) -> str:
        if count <= 0:
            return "0"
        if count == 1:
            return "1"
        if count == 2:
            return "2"
        return "3+"

    def _allow_count(self, count: int, filter_value):
        if filter_value is None:
            return True
        if filter_value == 3:
            return count >= 3
        return count == filter_value

    def handle(self, *args, **options):
        filter_count = options.get("data_plane_count")
        if filter_count not in (None, 0, 1, 2, 3):
            raise CommandError("data_plane_count should be one of: 0/1/2/3")

        gateway_count_map = {
            row["id"]: row["binding_count"]
            for row in Gateway.objects.annotate(binding_count=Count("data_plane_bindings")).values(
                "id", "binding_count"
            )
        }

        names_by_count = defaultdict(list)
        gateway_name_map = {row["id"]: row["name"] for row in Gateway.objects.values("id", "name")}

        for gateway_id, count in gateway_count_map.items():
            if not self._allow_count(count, filter_count):
                continue
            names_by_count[self._bucket_name(count)].append(gateway_name_map[gateway_id])

        if filter_count is None:
            ordered_buckets = ["0", "1", "2", "3+"]
        else:
            ordered_buckets = ["3+"] if filter_count == 3 else [str(filter_count)]

        for bucket in ordered_buckets:
            names = sorted(names_by_count.get(bucket, []))
            self.stdout.write(f"[{bucket}] count={len(names)}")
            for name in names:
                self.stdout.write(name)
