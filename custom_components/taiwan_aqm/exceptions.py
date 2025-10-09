"""Custom exceptions for Taiwan AQM integration."""

class TaiwanAQMError(Exception):
    """Base exception for Taiwan AQM errors"""


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
