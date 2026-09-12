from django.core.management.base import BaseCommand
from tenants.models import Tenant
from accounting.services import ChartOfAccountsSeederService


class Command(BaseCommand):
    help = "Seed default Chart of Accounts for a given tenant (for existing/old tenants only)"

    def add_arguments(self, parser):
        parser.add_argument("tenant_id", type=int)

    def handle(self, *args, **options):
        tenant = Tenant.objects.get(id=options["tenant_id"])
        ChartOfAccountsSeederService.seed_defaults(tenant)
        self.stdout.write(self.style.SUCCESS(f"Chart of Accounts seeded for tenant: {tenant.name}"))