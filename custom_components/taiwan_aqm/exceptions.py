"""Custom exceptions for Taiwan AQM integration."""

class TaiwanAQMError(Exception):
    """Base exception for Taiwan AQM errors"""
    def __init__(self, detail: dict = None):
        super().__init__(detail)
        self.detail = detail or {}

    def __getitem__(self, key):
        return self.detail.get(key)

    def __str__(self):
        return f"{self.__class__.__name__}({self.detail})"


class ApiAuthError(TaiwanAQMError):
    """API authentication failed"""
    

class DataNotFoundError(TaiwanAQMError):
    """No valid data found in the API response"""


class RecordNotFoundError(TaiwanAQMError):
    """No records found in the API response"""


class UnexpectedStatusError(TaiwanAQMError):
    """API returned unexpected status code"""


class RequestTimeoutError(TaiwanAQMError):
    """Request timed out"""


class RequestFailedError(TaiwanAQMError):
    """Request failed"""
