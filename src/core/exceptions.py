"""Custom exceptions cho hệ thống"""

class BaseWorkOSException(Exception):
    """Base exception class"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(message)

class LLMException(BaseWorkOSException):
    """Exception khi gọi LLM API"""
    pass

class ValidationException(BaseWorkOSException):
    """Exception khi validate input"""
    pass

class DocumentNotFoundException(BaseWorkOSException):
    """Exception khi không tìm thấy document"""
    pass

class TaskNotFoundException(BaseWorkOSException):
    """Exception khi không tìm thấy task"""
    pass

class RateLimitException(BaseWorkOSException):
    """Exception khi bị rate limit"""
    pass

class IntegrationException(BaseWorkOSException):
    """Exception cho third-party integrations"""
    pass