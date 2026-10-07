"""reset and fill the database with demo data"""

import hashlib

from django.core.management.base import BaseCommand
from django.db import connection

from pages.models import Account, Petition, Signature, AuditLog


def md5(pw: str) -> str:
    # weak on purpose, see FLAW 2 in views.py
    return hashlib.md5(pw.encode()).hexdigest()


class Command(BaseCommand):
    help = "wipe and seed demo data"

    def handle(self, *args, **options):
        for model in (Signature, Petition, Account, AuditLog):
            model.objects.all().delete()
        with connection.cursor() as cur:
            cur.execute("DELETE FROM sqlite_sequence WHERE name IN ('pages_petition','pages_account','pages_signature','pages_auditlog')")

        alice = Account.objects.create(username="alice", email="alice@example.org", password_hash=md5("sunshine"))
        bob = Account.objects.create(username="bob", email="bob@example.org", password_hash=md5("liverpool"))
        Account.objects.create(username="mallory", email="mallory@example.org", password_hash=md5("123456"))
        Account.objects.create(username="mod1", email="mod@example.org", password_hash=md5("Xq7!vatra9"), is_moderator=True)

        p1 = Petition.objects.create(owner=alice, title="30 km/h zone in the city centre", body="We ask the city to introduce a 30 km/h speed limit across the whole centre.")
        p2 = Petition.objects.create(owner=alice, title="More cycle paths along the Inn", body="Please extend the cycle paths along the river Inn.")
        p3 = Petition.objects.create(owner=bob, title="Public charging stations", body="We want more charging stations for electric cars in every district.")

        for name, mail in [("Eva Huber", "eva@example.org"), ("Tom Berg", "tom@example.org")]:
            Signature.objects.create(petition=p1, signer_name=name, signer_email=mail)
        Signature.objects.create(petition=p3, signer_name="Lea Fink", signer_email="lea@example.org")

        self.stdout.write(self.style.SUCCESS("seeded %d accounts, %d petitions" % (Account.objects.count(), Petition.objects.count())))
