import logging

from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Attachment

log = logging.getLogger(__name__)


@receiver(post_delete, sender=Attachment)
def remove_attachment_file(sender, instance, **kwargs):
    """Delete the private file once the row is gone – also for cascades and bulk deletes."""
    storage, name = instance.file.storage, instance.file.name
    if not name:
        return

    def _delete():
        try:
            storage.delete(name)
        except OSError:
            log.exception("Could not delete attachment file %s", name)

    # Only touch the disk if the database transaction really commits.
    transaction.on_commit(_delete)
