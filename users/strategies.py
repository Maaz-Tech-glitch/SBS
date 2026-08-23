from abc import ABC, abstractmethod
from django.contrib.auth import authenticate
from .repositories import UserRepository
from .exceptions import InvalidCredentialsException, UserNotFoundException


class AuthenticationStrategy(ABC):
    """Base authentication strategy"""
    
    @abstractmethod
    def authenticate(self, **credentials):
        pass


class UsernamePasswordStrategy(AuthenticationStrategy):
    """Username/password authentication"""
    
    def authenticate(self, username, password, **kwargs):
        """Authenticate with username/password"""
        try:
            user = UserRepository.get_by_username(username)
        except UserNotFoundException:
            raise InvalidCredentialsException()

        if not user.check_password(password):
            raise InvalidCredentialsException()

        return user


class EmailPasswordStrategy(AuthenticationStrategy):
    """Email/password authentication"""
    def authenticate(self, username, password, **kwargs):
        """Authenticate with email/password (username param mein email aata hai)"""
        try:
            user = UserRepository.get_by_email(username)
        except UserNotFoundException:
            raise InvalidCredentialsException()
        if not user.check_password(password):
            raise InvalidCredentialsException()
        return user

class AuthenticationFactory:
    """Factory for creating authentication strategies - OCP"""
    
    _strategies = {
        "username": UsernamePasswordStrategy(),
        "email": EmailPasswordStrategy(),
    }
    
    @classmethod
    def register_strategy(cls, name, strategy):
        """Register new strategy - extensible"""
        cls._strategies[name] = strategy
    
    @classmethod
    def get_strategy(cls, strategy_type="username"):
        """Get strategy instance"""
        return cls._strategies.get(strategy_type, UsernamePasswordStrategy())