class NotFoundError(Exception):
    def __init__(self, detail: str):
        self.detail = detail

class TokenError(Exception):
    pass

class InvalidTokenError(TokenError):
    pass

class ExpiredTokenError(TokenError):
    pass
