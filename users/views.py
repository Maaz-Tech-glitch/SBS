# from rest_framework import status

# from rest_framework.views import APIView

# from rest_framework.response import Response

# from rest_framework.permissions import (
#     IsAuthenticated,
# )

# from rest_framework.generics import (
#     ListCreateAPIView,
#     RetrieveUpdateDestroyAPIView,
# )

# from .permissions import IsAdmin

# from .serializers import (
#     CreateShopkeeperSerializer,
#     UserSerializer,
#     LoginSerializer,
#     UserModulePermissionUpdateSerializer,

#     ForgotPasswordSerializer,
#     VerifyPasswordOTPSerializer,
#     SetNewPasswordSerializer,

#     SignupOTPRequestSerializer,
#     SignupOTPVerifySerializer,
#     SignupSerializer,
# )

# from .models import User

# from .services import (
#     AuthenticationService,
#     TokenService,
#     LogoutService,
#     ResponseFormatterService,
#     ModulePermissionService,

#     PasswordResetService,
#     PasswordOTPVerificationService,
#     SetNewPasswordService,

#     SignupOTPService,
#     SignupService,
# )

# from config.pagination import (
#     CustomPagination,
# )

# from subscriptions.permissions import (
#     IsSubscriptionActive,
# )


# # =========================================================
# # BASE VIEW
# # =========================================================

# class BaseAPIView(APIView):

#     def success_response(
#         self,
#         data=None,
#         message="Success",
#         status_code=200
#     ):
#         response = {
#             "message": message
#         }

#         if data:
#             response["data"] = data

#         return Response(
#             response,
#             status=status_code
#         )

#     def error_response(
#         self,
#         error,
#         status_code=400
#     ):
#         return Response(
#             {
#                 "error": error
#             },
#             status=status_code
#         )


# # =========================================================
# # SIGNUP STEP 1
# # REQUEST OTP
# # =========================================================

# class SignupOTPRequestAPIView(
#     BaseAPIView
# ):
#     authentication_classes = []
#     permission_classes = []

#     def post(self, request):

#         serializer = (
#             SignupOTPRequestSerializer(
#                 data=request.data
#             )
#         )

#         serializer.is_valid(
#             raise_exception=True
#         )

#         result = (
#             SignupOTPService
#             .request_otp(
#                 **serializer.validated_data
#             )
#         )

#         return Response(
#             result,
#             status=status.HTTP_200_OK
#         )


# # =========================================================
# # SIGNUP STEP 2
# # VERIFY EMAIL ONLY
# # =========================================================

# class SignupOTPVerifyAPIView(
#     BaseAPIView
# ):
#     authentication_classes = []
#     permission_classes = []

#     def post(self, request):

#         serializer = (
#             SignupOTPVerifySerializer(
#                 data=request.data
#             )
#         )

#         serializer.is_valid(
#             raise_exception=True
#         )

#         result = (
#             SignupOTPService
#             .verify_otp(
#                 **serializer.validated_data
#             )
#         )

#         return Response(
#             result,
#             status=status.HTTP_200_OK
#         )


# # =========================================================
# # SIGNUP STEP 3
# # ACTUAL CREATE ACCOUNT
# # =========================================================

# class SignupAPIView(
#     BaseAPIView
# ):
#     authentication_classes = []
#     permission_classes = []

#     def post(self, request):

#         serializer = (
#             SignupSerializer(
#                 data=request.data
#             )
#         )

#         serializer.is_valid(
#             raise_exception=True
#         )

#         result = (
#             SignupService
#             .register(
#                 **serializer.validated_data
#             )
#         )

#         return Response(
#             result,
#             status=
#                 status.HTTP_201_CREATED
#         )


# # =========================================================
# # LOGIN
# # =========================================================

# class LoginAPIView(
#     BaseAPIView
# ):
#     authentication_classes = []
#     permission_classes = []

#     def post(self, request):

#         from subscriptions.services import (
#             SubscriptionService,
#         )

#         serializer = LoginSerializer(
#             data=request.data
#         )

#         serializer.is_valid(
#             raise_exception=True
#         )

#         data = (
#             serializer.validated_data
#         )

#         if data.get("email"):

#             user = (
#                 AuthenticationService
#                 .authenticate_user(
#                     username=
#                         data["email"],

#                     password=
#                         data["password"],

#                     strategy_type=
#                         "email"
#                 )
#             )

#         else:

#             user = (
#                 AuthenticationService
#                 .authenticate_user(
#                     username=
#                         data["username"],

#                     password=
#                         data["password"],

#                     strategy_type=
#                         "username"
#                 )
#             )

#         tokens = (
#             TokenService
#             .generate_tokens(user)
#         )

#         response_data = (
#             ResponseFormatterService
#             .format_login_response(
#                 user,
#                 tokens
#             )
#         )

#         response_data["subscription_active"] = (
#             SubscriptionService
#             .is_active(
#                 user.tenant
#             )
#         )
#         response_data["allowed_modules"] = ModulePermissionService.get_allowed_module_keys(user)

#         return Response(
#             response_data,
#             status=status.HTTP_200_OK
#         )


# # =========================================================
# # LOGOUT
# # =========================================================

# class LogoutAPIView(
#     BaseAPIView
# ):
#     permission_classes = [
#         IsAuthenticated
#     ]

#     def post(self, request):

#         refresh_token = (
#             request.data.get(
#                 "refresh"
#             )
#         )

#         LogoutService.logout_user(
#             refresh_token
#         )

#         return self.success_response(
#             message=
#                 "Logout Successful"
#         )


# # =========================================================
# # USERS
# # =========================================================

# class UserListCreateAPIView(
#     ListCreateAPIView
# ):
#     permission_classes = [
#         IsAuthenticated,
#         IsAdmin,
#         IsSubscriptionActive,
#     ]

#     pagination_class = (
#         CustomPagination
#     )

#     def get_serializer_class(
#         self
#     ):
#         if (
#             self.request.method
#             == "POST"
#         ):
#             return (
#                 CreateShopkeeperSerializer
#             )

#         return UserSerializer

#     def get_queryset(self):

#         queryset = (
#             User.objects.filter(
#                 tenant=
#                     self.request
#                     .user
#                     .tenant
#             )
#         )

#         search = (
#             self.request
#             .query_params
#             .get("search")
#         )

#         if search:
#             queryset = (
#                 queryset.filter(
#                     username__icontains=
#                         search
#                 )
#             )

#         role = (
#             self.request
#             .query_params
#             .get("role")
#         )

#         if role:
#             queryset = (
#                 queryset.filter(
#                     role=
#                         role.lower()
#                 )
#             )

#         ordering = (
#             self.request
#             .query_params
#             .get("ordering")
#         )

#         if ordering in (
#             "id",
#             "-id",
#             "username",
#             "-username",
#         ):
#             queryset = (
#                 queryset.order_by(
#                     ordering
#                 )
#             )

#         return queryset

#     def create(
#         self,
#         request,
#         *args,
#         **kwargs
#     ):
#         from subscriptions.services import (
#             SubscriptionService,
#         )

#         from subscriptions.exceptions import (
#             NoActiveSubscriptionException,
#         )

#         from .exceptions import (
#             UserLimitExceededException,
#         )

#         tenant = (
#             request.user.tenant
#         )

#         if not (
#             SubscriptionService
#             .is_active(tenant)
#         ):
#             raise (
#                 NoActiveSubscriptionException()
#             )

#         current_count = (
#             User.objects.filter(
#                 tenant=tenant
#             ).count()
#         )

#         max_users = (
#             SubscriptionService
#             .get_max_users_for_tenant(
#                 tenant
#             )
#         )

#         if (
#             current_count
#             >= max_users
#         ):
#             raise (
#                 UserLimitExceededException()
#             )

#         serializer = (
#             self.get_serializer(
#                 data=request.data
#             )
#         )

#         serializer.is_valid(
#             raise_exception=True
#         )

#         user = serializer.save(
#             tenant=tenant
#         )

#         return Response(
#             {
#                 "message":
#                     "User Created Successfully",

#                 "data":
#                     UserSerializer(
#                         user
#                     ).data,
#             },

#             status=
#                 status.HTTP_201_CREATED
#         )


# class UserDetailAPIView(
#     RetrieveUpdateDestroyAPIView
# ):
#     serializer_class = (
#         UserSerializer
#     )

#     permission_classes = [
#         IsAuthenticated,
#         IsAdmin,
#     ]

#     def get_queryset(self):

#         tenant = (
#             self.request.user.tenant
#         )

#         if not tenant:
#             return User.objects.none()

#         return User.objects.filter(
#             tenant=tenant
#         )


# class UserModulePermissionAPIView(APIView):
#     permission_classes = [IsAuthenticated, IsAdmin]

#     def get(self, request, user_id):
#         target_user = User.objects.filter(
#             id=user_id,
#             tenant=request.user.tenant,
#         ).first()

#         if not target_user:
#             return Response(
#                 {"detail": "User not found in your shop."},
#                 status=status.HTTP_404_NOT_FOUND,
#             )

#         if target_user.role != "shopkeeper":
#             return Response(
#                 {"detail": "Module permissions are only available for shopkeepers."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         return Response(
#             {
#                 "user": {
#                     "id": target_user.id,
#                     "username": target_user.username,
#                     "role": target_user.role,
#                 },
#                 "modules": ModulePermissionService.get_user_module_status(target_user),
#             },
#             status=status.HTTP_200_OK,
#         )

#     def put(self, request, user_id):
#         target_user = User.objects.filter(
#             id=user_id,
#             tenant=request.user.tenant,
#         ).first()

#         if not target_user:
#             return Response(
#                 {"detail": "User not found in your shop."},
#                 status=status.HTTP_404_NOT_FOUND,
#             )

#         if target_user.role != "shopkeeper":
#             return Response(
#                 {"detail": "Module permissions can only be assigned to shopkeepers."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         serializer = UserModulePermissionUpdateSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         try:
#             modules = ModulePermissionService.set_user_permissions(
#                 request.user,
#                 target_user,
#                 serializer.validated_data["modules"],
#             )
#         except ValueError as exc:
#             return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

#         return Response(
#             {
#                 "message": "User module permissions updated successfully.",
#                 "modules": modules,
#             },
#             status=status.HTTP_200_OK,
#         )


# # =========================================================
# # PASSWORD RESET
# # =========================================================

# class ForgotPasswordAPIView(
#     BaseAPIView
# ):
#     authentication_classes = []
#     permission_classes = []

#     def post(self, request):

#         serializer = (
#             ForgotPasswordSerializer(
#                 data=request.data
#             )
#         )

#         serializer.is_valid(
#             raise_exception=True
#         )

#         result = (
#             PasswordResetService
#             .request_password_reset(
#                 serializer
#                 .validated_data[
#                     "email"
#                 ]
#             )
#         )

#         return Response(
#             result,
#             status=status.HTTP_200_OK
#         )


# class VerifyPasswordOTPAPIView(
#     BaseAPIView
# ):
#     authentication_classes = []
#     permission_classes = []

#     def post(self, request):

#         serializer = (
#             VerifyPasswordOTPSerializer(
#                 data=request.data
#             )
#         )

#         serializer.is_valid(
#             raise_exception=True
#         )

#         result = (
#             PasswordOTPVerificationService
#             .verify(
#                 **serializer.validated_data
#             )
#         )

#         return Response(
#             result,
#             status=status.HTTP_200_OK
#         )


# class SetNewPasswordAPIView(
#     BaseAPIView
# ):
#     authentication_classes = []
#     permission_classes = []

#     def post(self, request):

#         serializer = (
#             SetNewPasswordSerializer(
#                 data=request.data
#             )
#         )

#         serializer.is_valid(
#             raise_exception=True
#         )

#         result = (
#             SetNewPasswordService
#             .set_password(
#                 **serializer.validated_data
#             )
#         )

#         return Response(
#             result,
#             status=status.HTTP_200_OK
#         )

from django.db import transaction

from rest_framework import status

from rest_framework.views import APIView

from rest_framework.response import Response

from rest_framework.permissions import (
    IsAuthenticated,
)

from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)

from .permissions import IsAdmin

from .serializers import (
    CreateShopkeeperSerializer,
    UserSerializer,
    LoginSerializer,
    UserModulePermissionUpdateSerializer,

    ForgotPasswordSerializer,
    VerifyPasswordOTPSerializer,
    SetNewPasswordSerializer,

    SignupOTPRequestSerializer,
    SignupOTPVerifySerializer,
    SignupSerializer,
)

from .models import User
from .notification_handlers import UserNotificationService

from .services import (
    AuthenticationService,
    TokenService,
    LogoutService,
    ResponseFormatterService,
    ModulePermissionService,

    PasswordResetService,
    PasswordOTPVerificationService,
    SetNewPasswordService,

    SignupOTPService,
    SignupService,
)

from config.pagination import (
    CustomPagination,
)

from subscriptions.permissions import (
    IsSubscriptionActive,
)


# =========================================================
# BASE VIEW
# =========================================================

class BaseAPIView(APIView):

    def success_response(
        self,
        data=None,
        message="Success",
        status_code=200
    ):
        response = {
            "message": message
        }

        if data:
            response["data"] = data

        return Response(
            response,
            status=status_code
        )

    def error_response(
        self,
        error,
        status_code=400
    ):
        return Response(
            {
                "error": error
            },
            status=status_code
        )


# =========================================================
# SIGNUP STEP 1
# REQUEST OTP
# =========================================================

class SignupOTPRequestAPIView(
    BaseAPIView
):
    authentication_classes = []
    permission_classes = []

    def post(self, request):

        serializer = (
            SignupOTPRequestSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        result = (
            SignupOTPService
            .request_otp(
                **serializer.validated_data
            )
        )

        return Response(
            result,
            status=status.HTTP_200_OK
        )


# =========================================================
# SIGNUP STEP 2
# VERIFY EMAIL ONLY
# =========================================================

class SignupOTPVerifyAPIView(
    BaseAPIView
):
    authentication_classes = []
    permission_classes = []

    def post(self, request):

        serializer = (
            SignupOTPVerifySerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        result = (
            SignupOTPService
            .verify_otp(
                **serializer.validated_data
            )
        )

        return Response(
            result,
            status=status.HTTP_200_OK
        )


# =========================================================
# SIGNUP STEP 3
# ACTUAL CREATE ACCOUNT
# =========================================================

class SignupAPIView(
    BaseAPIView
):
    authentication_classes = []
    permission_classes = []

    def post(self, request):

        serializer = (
            SignupSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        result = (
            SignupService
            .register(
                **serializer.validated_data
            )
        )

        return Response(
            result,
            status=
                status.HTTP_201_CREATED
        )


# =========================================================
# LOGIN
# =========================================================

class LoginAPIView(
    BaseAPIView
):
    authentication_classes = []
    permission_classes = []

    def post(self, request):

        from subscriptions.services import (
            SubscriptionService,
        )

        serializer = LoginSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = (
            serializer.validated_data
        )

        if data.get("email"):

            user = (
                AuthenticationService
                .authenticate_user(
                    username=
                        data["email"],

                    password=
                        data["password"],

                    strategy_type=
                        "email"
                )
            )

        else:

            user = (
                AuthenticationService
                .authenticate_user(
                    username=
                        data["username"],

                    password=
                        data["password"],

                    strategy_type=
                        "username"
                )
            )

        tokens = (
            TokenService
            .generate_tokens(user)
        )

        response_data = (
            ResponseFormatterService
            .format_login_response(
                user,
                tokens
            )
        )

        response_data["subscription_active"] = (
            SubscriptionService
            .is_active(
                user.tenant
            )
        )
        response_data["allowed_modules"] = ModulePermissionService.get_allowed_module_keys(user)

        UserNotificationService.schedule_login(
            user=user,
            login_method=(
                "EMAIL"
                if data.get("email")
                else "USERNAME"
            ),
        )

        return Response(
            response_data,
            status=status.HTTP_200_OK
        )


# =========================================================
# LOGOUT
# =========================================================

class LogoutAPIView(
    BaseAPIView
):
    permission_classes = [
        IsAuthenticated
    ]

    def post(self, request):

        refresh_token = (
            request.data.get(
                "refresh"
            )
        )

        LogoutService.logout_user(
            refresh_token
        )

        UserNotificationService.schedule_logout(
            user=request.user,
        )

        return self.success_response(
            message=
                "Logout Successful"
        )


# =========================================================
# USERS
# =========================================================

class UserListCreateAPIView(
    ListCreateAPIView
):
    permission_classes = [
        IsAuthenticated,
        IsAdmin,
        IsSubscriptionActive,
    ]

    pagination_class = (
        CustomPagination
    )

    def get_serializer_class(
        self
    ):
        if (
            self.request.method
            == "POST"
        ):
            return (
                CreateShopkeeperSerializer
            )

        return UserSerializer

    def get_queryset(self):

        queryset = (
            User.objects.filter(
                tenant=
                    self.request
                    .user
                    .tenant
            )
        )

        search = (
            self.request
            .query_params
            .get("search")
        )

        if search:
            queryset = (
                queryset.filter(
                    username__icontains=
                        search
                )
            )

        role = (
            self.request
            .query_params
            .get("role")
        )

        if role:
            queryset = (
                queryset.filter(
                    role=
                        role.lower()
                )
            )

        ordering = (
            self.request
            .query_params
            .get("ordering")
        )

        if ordering in (
            "id",
            "-id",
            "username",
            "-username",
        ):
            queryset = (
                queryset.order_by(
                    ordering
                )
            )

        return queryset

    def create(
        self,
        request,
        *args,
        **kwargs
    ):
        from subscriptions.services import (
            SubscriptionService,
        )

        from subscriptions.exceptions import (
            NoActiveSubscriptionException,
        )

        from .exceptions import (
            UserLimitExceededException,
        )

        tenant = (
            request.user.tenant
        )

        if not (
            SubscriptionService
            .is_active(tenant)
        ):
            exc = NoActiveSubscriptionException()

            UserNotificationService.schedule_failure(
                tenant=tenant,
                actor=request.user,
                operation="CREATE",
                error=exc,
            )

            raise exc

        current_count = (
            User.objects.filter(
                tenant=tenant
            ).count()
        )

        max_users = (
            SubscriptionService
            .get_max_users_for_tenant(
                tenant
            )
        )

        if (
            current_count
            >= max_users
        ):
            exc = UserLimitExceededException()

            UserNotificationService.schedule_failure(
                tenant=tenant,
                actor=request.user,
                operation="CREATE",
                error=exc,
            )

            raise exc

        serializer = (
            self.get_serializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            with transaction.atomic():
                user = serializer.save(
                    tenant=tenant
                )

                UserNotificationService.schedule_user_created(
                    target_user=user,
                    actor=request.user,
                )

        except Exception as exc:
            UserNotificationService.schedule_failure(
                tenant=tenant,
                actor=request.user,
                operation="CREATE",
                error=exc,
            )
            raise

        return Response(
            {
                "message":
                    "User Created Successfully",

                "data":
                    UserSerializer(
                        user
                    ).data,
            },

            status=
                status.HTTP_201_CREATED
        )


class UserDetailAPIView(
    RetrieveUpdateDestroyAPIView
):
    serializer_class = (
        UserSerializer
    )

    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]

    def get_queryset(self):

        tenant = (
            self.request.user.tenant
        )

        if not tenant:
            return User.objects.none()

        return User.objects.filter(
            tenant=tenant
        )

    def perform_update(self, serializer):
        target_before = serializer.instance

        changed_fields = [
            field
            for field, value in serializer.validated_data.items()
            if getattr(target_before, field, None) != value
        ]

        try:
            with transaction.atomic():
                target_user = serializer.save()

                UserNotificationService.schedule_user_updated(
                    target_user=target_user,
                    actor=self.request.user,
                    changed_fields=changed_fields,
                )

        except Exception as exc:
            UserNotificationService.schedule_failure(
                tenant=self.request.user.tenant,
                actor=self.request.user,
                operation="UPDATE",
                error=exc,
                target_user=target_before,
            )
            raise

    def perform_destroy(self, instance):
        tenant = self.request.user.tenant
        actor = self.request.user

        target_user_data = (
            UserNotificationService
            ._safe_user_data(instance)
        )

        try:
            with transaction.atomic():
                instance.delete()

                UserNotificationService.schedule_user_deleted(
                    tenant=tenant,
                    actor=actor,
                    target_user_data=target_user_data,
                )

        except Exception as exc:
            UserNotificationService.schedule_failure(
                tenant=tenant,
                actor=actor,
                operation="DELETE",
                error=exc,
                target_user=instance,
            )
            raise


class UserModulePermissionAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, user_id):
        target_user = User.objects.filter(
            id=user_id,
            tenant=request.user.tenant,
        ).first()

        if not target_user:
            return Response(
                {"detail": "User not found in your shop."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if target_user.role != "shopkeeper":
            return Response(
                {"detail": "Module permissions are only available for shopkeepers."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "user": {
                    "id": target_user.id,
                    "username": target_user.username,
                    "role": target_user.role,
                },
                "modules": ModulePermissionService.get_user_module_status(target_user),
            },
            status=status.HTTP_200_OK,
        )

    def put(self, request, user_id):
        target_user = User.objects.filter(
            id=user_id,
            tenant=request.user.tenant,
        ).first()

        if not target_user:
            UserNotificationService.schedule_failure(
                tenant=request.user.tenant,
                actor=request.user,
                operation="MODULE_PERMISSIONS_UPDATE",
                error="User not found in your shop.",
            )

            return Response(
                {"detail": "User not found in your shop."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if target_user.role != "shopkeeper":
            UserNotificationService.schedule_failure(
                tenant=request.user.tenant,
                actor=request.user,
                operation="MODULE_PERMISSIONS_UPDATE",
                error="Module permissions can only be assigned to shopkeepers.",
                target_user=target_user,
            )

            return Response(
                {"detail": "Module permissions can only be assigned to shopkeepers."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = UserModulePermissionUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            modules = ModulePermissionService.set_user_permissions(
                request.user,
                target_user,
                serializer.validated_data["modules"],
            )
        except ValueError as exc:
            UserNotificationService.schedule_failure(
                tenant=request.user.tenant,
                actor=request.user,
                operation="MODULE_PERMISSIONS_UPDATE",
                error=exc,
                target_user=target_user,
            )

            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "message": "User module permissions updated successfully.",
                "modules": modules,
            },
            status=status.HTTP_200_OK,
        )


# =========================================================
# PASSWORD RESET
# =========================================================

class ForgotPasswordAPIView(
    BaseAPIView
):
    authentication_classes = []
    permission_classes = []

    def post(self, request):

        serializer = (
            ForgotPasswordSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        result = (
            PasswordResetService
            .request_password_reset(
                serializer
                .validated_data[
                    "email"
                ]
            )
        )

        return Response(
            result,
            status=status.HTTP_200_OK
        )


class VerifyPasswordOTPAPIView(
    BaseAPIView
):
    authentication_classes = []
    permission_classes = []

    def post(self, request):

        serializer = (
            VerifyPasswordOTPSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        result = (
            PasswordOTPVerificationService
            .verify(
                **serializer.validated_data
            )
        )

        return Response(
            result,
            status=status.HTTP_200_OK
        )


class SetNewPasswordAPIView(
    BaseAPIView
):
    authentication_classes = []
    permission_classes = []

    def post(self, request):

        serializer = (
            SetNewPasswordSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        result = (
            SetNewPasswordService
            .set_password(
                **serializer.validated_data
            )
        )

        return Response(
            result,
            status=status.HTTP_200_OK
        )