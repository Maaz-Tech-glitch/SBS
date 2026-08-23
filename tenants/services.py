from .repositories import TenantRepository
from .exceptions import TenantAlreadyExistsException


class TenantService:
    @staticmethod
    def create_tenant(name, address=None, business_type=None):
        return TenantRepository.create(name=name, address=address, business_type=business_type)

    @staticmethod
    def get_tenant(tenant_id):
        return TenantRepository.get_by_id(tenant_id)

    @staticmethod
    def setup_shop(user, name, address=None, business_type=None):
        if user.tenant_id:
            raise TenantAlreadyExistsException()
        tenant = TenantRepository.create(name=name, address=address, business_type=business_type)
        user.tenant = tenant
        user.save(update_fields=["tenant"])
        return tenant