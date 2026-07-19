"""CurrentUserImpersonate — context manager wrapping every file/UNC access.

In the desk (HSBC) environment this impersonates the current interactive user so
that access to UNC shares (\\\\host\\...\\HistoDatas\\...) uses their credentials.

Here it is a safe no-op integration point: real Win32 impersonation
(LogonUser + ImpersonateLoggedOnUser via pywin32) can be plugged behind the same
`with CurrentUserImpersonate():` interface without touching any call site.
"""


class CurrentUserImpersonate:
    def __enter__(self) -> "CurrentUserImpersonate":
        # TODO(desk): real impersonation via pywin32 in the HSBC environment.
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        # Do not suppress exceptions from the wrapped file/UNC access.
        return False
