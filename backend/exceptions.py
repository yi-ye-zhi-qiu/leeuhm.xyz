class FailedRequest(Exception):
    def __init__(self, message: str = "invalid request"):
        super().__init__(message)
