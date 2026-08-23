from .models import Tenant
from .exceptions import TenantNotFoundException


class TenantRepository:
    @staticmethod
    def get_by_id(tenant_id):
        try:
            return Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            raise TenantNotFoundException()

    @staticmethod
    def create(name, address, business_type):
        return Tenant.objects.create(
            name=name, address=address or "", business_type=business_type or ""
        )