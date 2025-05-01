'''
State and Args context management with centralized authentication.
Provides stack-based contexts that rely on a single AuthManager to generate, verify, and revoke tokens.
'''
from dataclasses import dataclass
from threading import local
from typing import Optional, List
import secrets
import uuid


class AuthManager:
    """
    Centralized token management for all contexts.
    """
    _valid_tokens: set[str] = set()

    @classmethod
    def generate_token(cls) -> str:
        """
        Create and register a new secure token.
        """
        auth_token = secrets.token_hex(16)
        cls._valid_tokens.add(auth_token)
        return auth_token

    @classmethod
    def verify_token(cls, auth_token: str) -> bool:
        """
        Check if the token is valid.
        """
        return auth_token in cls._valid_tokens

    @classmethod
    def revoke_token(cls, auth_token: str) -> None:
        """
        Invalidate a token so it can no longer be used.
        """
        cls._valid_tokens.discard(auth_token)


@dataclass(frozen=True)
class StateSnapshot:
    """
    Immutable snapshot of the sys context.
    """
    debug: bool
    log_to_db: bool
    log_level: int
    token: str


@dataclass(frozen=True)
class ArgsSnapshot:
    """
    Immutable snapshot of the args context.
    """
    clear: bool
    debug: bool
    db: bool
    db_path: str
    log_to_db: bool
    get_logs: int
    export: str
    log_level: int
    token: str


class BaseContext:
    """
    Base for context stacks with token verification.
    """
    _local = local()
    _stack_name: str
    _snapshot_type: type

    @classmethod
    def _init_stack(cls):
        if not hasattr(cls._local, cls._stack_name):
            setattr(cls._local, cls._stack_name, [])  # type: ignore

    @classmethod
    def _current(cls):
        cls._init_stack()
        stack = getattr(cls._local, cls._stack_name)
        return stack[-1] if stack else None

    @classmethod
    def _push(cls, snapshot):
        cls._init_stack()
        getattr(cls._local, cls._stack_name).append(snapshot)

    @classmethod
    def _pop(cls, auth_token: str):
        cls._init_stack()
        stack = getattr(cls._local, cls._stack_name)
        if not stack:
            raise RuntimeError(f"No {cls.__name__} to pop.")
        current = stack[-1]
        if current.token != auth_token or not AuthManager.verify_token(auth_token):
            raise PermissionError(f"Invalid token for {cls.__name__} pop.")
        stack.pop()


class SysContext(BaseContext):
    """
    System-level context for debug and logging state.
    """
    _stack_name = uuid.uuid4().hex

    @classmethod
    def get_debug(cls) -> bool:
        state = cls._current()
        return state.debug if state else False

    @classmethod
    def get_log_to_db(cls) -> bool:
        state = cls._current()
        return state.log_to_db if state else False

    @classmethod
    def get_log_level(cls) -> int:
        state = cls._current()
        return state.log_level if state else 10

    @classmethod
    def push(
            cls, *,
            auth_token: str,
            debug: Optional[bool] = None,
            log_to_db: Optional[bool] = None,
            log_level: Optional[int] = None):
        if not AuthManager.verify_token(auth_token):
            raise PermissionError("Invalid token for SysContext push.")
        base = cls._current() or StateSnapshot(False, False, 1, auth_token)
        debug_flag = debug if debug is not None else base.debug
        level = 0 if debug_flag else (
            log_level if log_level is not None else base.log_level)
        if not isinstance(level, int) or not 10 <= level <= 50:
            level = 10
        snapshot = StateSnapshot(
            debug_flag,
            log_to_db if log_to_db is not None else base.log_to_db,
            level,
            auth_token
        )
        cls._push(snapshot)

    @classmethod
    def pop(cls, auth_token: str):
        cls._pop(auth_token)


class ArgsContext(BaseContext):
    """
    Argument parsing context for CLI flags.
    """
    _stack_name = uuid.uuid4().hex

    @classmethod
    def get(cls) -> ArgsSnapshot:
        current = cls._current()
        if current:
            return current
        return ArgsSnapshot(False, False, False, 'logs.db', False, 0, '', 10, '')

    @classmethod
    def push(cls, *, auth_token: str, clear: Optional[bool] = None,
             debug: Optional[bool] = None, db: Optional[bool] = None,
             db_path: Optional[str] = None, log_to_db: Optional[bool] = None,
             get_logs: Optional[int] = None, export: Optional[str] = None,
             log_level: Optional[int] = None):
        if not AuthManager.verify_token(auth_token):
            raise PermissionError("Invalid token for ArgsContext push.")
        base = cls._current() or ArgsSnapshot(
            False, False, False, 'logs.db', False, 0, '', 10, auth_token)
        snapshot = ArgsSnapshot(
            clear=clear if clear is not None else base.clear,
            debug=debug if debug is not None else base.debug,
            db=db if db is not None else base.db,
            db_path=db_path if db_path is not None else base.db_path,
            log_to_db=log_to_db if log_to_db is not None else base.log_to_db,
            get_logs=get_logs if get_logs is not None else base.get_logs,
            export=export if export is not None else base.export,
            log_level=log_level if log_level is not None else base.log_level,
            token=auth_token
        )
        cls._push(snapshot)

    @classmethod
    def pop(cls, auth_token: str):
        cls._pop(auth_token)


if __name__ == "__main__":
    # Centralized token handling
    token = AuthManager.generate_token()

    # SysContext demonstration
    SysContext.push(auth_token=token, debug=True)
    print(SysContext.get_debug(), SysContext.get_log_level())
    SysContext.pop(auth_token=token)

    # ArgsContext demonstration
    ArgsContext.push(auth_token=token, debug=True, get_logs=5)
    args = ArgsContext.get()
    print(args.debug, args.get_logs)
    ArgsContext.pop(token)

    # Revoke when done
    AuthManager.revoke_token(token)
