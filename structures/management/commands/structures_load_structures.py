from django.core.management import call_command
from django.core.management.base import BaseCommand

from allianceauth.services.hooks import get_extension_logger
from app_utils.logging import LoggerAddTag

from ... import __title__

logger = LoggerAddTag(get_extension_logger(__name__), __title__)

EVE_STRUCTURE_CATEGORY = 65


class Command(BaseCommand):
    help = "Preloads data required for this app from ESI"

    def handle(self, *args, **options):
        call_command(
            "eveuniverse_load_types",
            __title__,
            "--category_id_with_dogma",
            str(EVE_STRUCTURE_CATEGORY),
        )
