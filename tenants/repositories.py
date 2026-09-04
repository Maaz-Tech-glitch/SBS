from .models import Tenant
from .exceptions import TenantNotFoundException, TenantAlreadyExistsException


class TenantRepository:
    @staticmethod
    def get_by_id(tenant_id):
        try:
            return Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            raise TenantNotFoundException()

    @staticmethod
    def create(name, email, phone=None, address=None, business_type=None):
        if Tenant.objects.filter(name=name).exists():
            raise TenantAlreadyExistsException()
        return Tenant.objects.create(
            name=name, email=email, phone=phone or "",
            address=address or "", business_type=business_type or ""
        )
    @staticmethod
    def update(tenant, **fields):
        allowed_fields = ["address", "business_type", "phone"]
        for key, value in fields.items():
            if key in allowed_fields and value is not None:
                setattr(tenant, key, value)
        tenant.save(update_fields=[f for f in fields if f in allowed_fields] + ["updated_at"])
        return tenant