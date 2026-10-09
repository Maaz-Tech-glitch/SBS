from django.db import transaction

from notifications.models import Notification
from notifications.services import NotificationService


class UserNotificationService:
    USER_ACTION_URL = "/users"
    DASHBOARD_ACTION_URL = "/dashboard"

    @staticmethod
    def _schedule(callback):
        transaction.on_commit(
            callback,
            robust=True,
        )

    @staticmethod
    def _safe_user_data(user):
        if user is None:
            return {}

        return {
            "user_id": getattr(user, "pk", None),
            "username": getattr(user, "username", ""),
            "email": getattr(user, "email", ""),
            "role": getattr(user, "role", ""),
        }

    @classmethod
    def schedule_admin_account_created(cls, *, user):
        tenant = user.tenant
        user_data = cls._safe_user_data(user)

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=user,
                title="Admin Account Created",
                message=f"{user.username} created the shop admin account.",
                event_type="ADMIN_ACCOUNT_CREATED",
                level=Notification.Level.SUCCESS,
                entity_type="USER",
                entity_id=user.pk,
                action_url=cls.DASHBOARD_ACTION_URL,
                metadata=user_data,
            )

        cls._schedule(create_notification)

    @classmethod
    def schedule_login(cls, *, user, login_method):
        if user.tenant_id is None:
            return

        tenant = user.tenant
        user_data = cls._safe_user_data(user)
        login_method = str(login_method or "").upper()

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=user,
                title="User Login",
                message=f"{user.username} logged in successfully.",
                event_type="USER_LOGIN",
                level=Notification.Level.INFO,
                entity_type="USER",
                entity_id=user.pk,
                action_url=cls.USER_ACTION_URL,
                metadata={
                    **user_data,
                    "login_method": login_method,
                },
            )

        cls._schedule(create_notification)

    @classmethod
    def schedule_logout(cls, *, user):
        if user.tenant_id is None:
            return

        tenant = user.tenant
        user_data = cls._safe_user_data(user)

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=user,
                title="User Logout",
                message=f"{user.username} logged out successfully.",
                event_type="USER_LOGOUT",
                level=Notification.Level.INFO,
                entity_type="USER",
                entity_id=user.pk,
                action_url=cls.USER_ACTION_URL,
                metadata=user_data,
            )

        cls._schedule(create_notification)

    @classmethod
    def schedule_user_created(cls, *, target_user, actor):
        tenant = target_user.tenant
        user_data = cls._safe_user_data(target_user)

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=actor,
                title="User Created",
                message=f"{target_user.username} was created successfully.",
                event_type="USER_CREATED",
                level=Notification.Level.SUCCESS,
                entity_type="USER",
                entity_id=target_user.pk,
                action_url=cls.USER_ACTION_URL,
                metadata=user_data,
            )

        cls._schedule(create_notification)

    @classmethod
    def schedule_user_updated(
        cls,
        *,
        target_user,
        actor,
        changed_fields,
    ):
        fields = sorted(set(changed_fields or []))
        if not fields:
            return

        tenant = target_user.tenant
        user_data = cls._safe_user_data(target_user)

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=actor,
                title="User Updated",
                message=f"{target_user.username} was updated successfully.",
                event_type="USER_UPDATED",
                level=Notification.Level.INFO,
                entity_type="USER",
                entity_id=target_user.pk,
                action_url=cls.USER_ACTION_URL,
                metadata={
                    **user_data,
                    "changed_fields": fields,
                },
            )

        cls._schedule(create_notification)

    @classmethod
    def schedule_user_deleted(
        cls,
        *,
        tenant,
        actor,
        target_user_data,
    ):
        target_id = target_user_data.get("user_id", "")
        username = target_user_data.get("username", "User")

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=actor,
                title="User Deleted",
                message=f"{username} was deleted successfully.",
                event_type="USER_DELETED",
                level=Notification.Level.WARNING,
                entity_type="USER",
                entity_id=target_id,
                action_url=cls.USER_ACTION_URL,
                metadata=target_user_data,
            )

        cls._schedule(create_notification)

    @classmethod
    def schedule_module_permissions_updated(
        cls,
        *,
        target_user,
        actor,
        previous_modules,
        new_modules,
    ):
        tenant = target_user.tenant
        user_data = cls._safe_user_data(target_user)

        previous_set = set(previous_modules or [])
        new_set = set(new_modules or [])

        granted = sorted(new_set - previous_set)
        revoked = sorted(previous_set - new_set)

        if not granted and not revoked:
            return

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=actor,
                title="User Permissions Updated",
                message=f"Module access for {target_user.username} was updated.",
                event_type="USER_MODULE_PERMISSIONS_UPDATED",
                level=Notification.Level.INFO,
                entity_type="USER",
                entity_id=target_user.pk,
                action_url=cls.USER_ACTION_URL,
                metadata={
                    **user_data,
                    "granted_modules": granted,
                    "revoked_modules": revoked,
                    "allowed_modules": sorted(new_set),
                },
            )

        cls._schedule(create_notification)

    @classmethod
    def schedule_password_reset_requested(cls, *, user):
        if user.tenant_id is None:
            return

        tenant = user.tenant
        user_data = cls._safe_user_data(user)

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=user,
                title="Password Reset Requested",
                message=f"A password reset was requested for {user.username}.",
                event_type="PASSWORD_RESET_REQUESTED",
                level=Notification.Level.WARNING,
                entity_type="USER",
                entity_id=user.pk,
                action_url=cls.USER_ACTION_URL,
                metadata=user_data,
            )

        cls._schedule(create_notification)

    @classmethod
    def schedule_password_reset_otp_verified(cls, *, user):
        if user.tenant_id is None:
            return

        tenant = user.tenant
        user_data = cls._safe_user_data(user)

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=user,
                title="Password Reset Verified",
                message=f"Password reset verification succeeded for {user.username}.",
                event_type="PASSWORD_RESET_OTP_VERIFIED",
                level=Notification.Level.INFO,
                entity_type="USER",
                entity_id=user.pk,
                action_url=cls.USER_ACTION_URL,
                metadata=user_data,
            )

        cls._schedule(create_notification)

    @classmethod
    def schedule_password_changed(cls, *, user):
        if user.tenant_id is None:
            return

        tenant = user.tenant
        user_data = cls._safe_user_data(user)

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=user,
                title="Password Changed",
                message=f"Password for {user.username} was changed successfully.",
                event_type="PASSWORD_CHANGED",
                level=Notification.Level.WARNING,
                entity_type="USER",
                entity_id=user.pk,
                action_url=cls.USER_ACTION_URL,
                metadata=user_data,
            )

        cls._schedule(create_notification)

    @classmethod
    def schedule_failure(
        cls,
        *,
        tenant,
        actor,
        operation,
        error,
        target_user=None,
    ):
        if tenant is None:
            return

        operation = str(operation or "USER_OPERATION").upper()
        target_data = cls._safe_user_data(target_user)
        safe_error = str(error)[:300]
        username = target_data.get("username", "")

        def create_notification():
            NotificationService.create(
                tenant=tenant,
                actor=actor,
                title="User Operation Failed",
                message=(
                    f"{operation.replace('_', ' ').title()} failed"
                    + (f" for {username}." if username else ".")
                ),
                event_type=f"USER_{operation}_FAILED",
                level=Notification.Level.ERROR,
                entity_type="USER",
                entity_id=target_data.get("user_id", ""),
                action_url=cls.USER_ACTION_URL,
                metadata={
                    **target_data,
                    "error": safe_error,
                },
            )

        cls._schedule(create_notification)
