from .repositories import TenantRepository
from .exceptions import TenantAlreadyExistsException


class TenantService:
    @staticmethod
    def create_tenant(name, email, phone=None, address=None, business_type=None):
        from accounting.services import ChartOfAccountsSeederService

        tenant = TenantRepository.create(
            name=name, email=email, phone=phone,
            address=address, business_type=business_type
        )
        ChartOfAccountsSeederService.seed_defaults(tenant) 
        return tenant

    @staticmethod
    def get_tenant(tenant_id):
        return TenantRepository.get_by_id(tenant_id)
    @staticmethod
    def update_tenant(tenant, **fields):
        return TenantRepository.update(tenant, **fields)