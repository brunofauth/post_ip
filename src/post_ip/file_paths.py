# vim: foldmethod=marker foldlevel=0
from __future__ import annotations
# yapf: disable

from pathlib import Path
import os


# get_config_home_fp() {{{

_config_home: Path | None = None
def get_config_home_fp() -> Path:
    global _config_home
    if _config_home is None:
        _config_home = _get_config_home_fp()
        _config_home.mkdir(parents=True, exist_ok=True)
    return _config_home


def _get_config_home_fp() -> Path:
    if (config_home := os.environ.get("XDG_CONFIG_HOME", None)) is not None:
        return Path(config_home) / "post-ip"
    if (home := os.environ.get("HOME", None)) is not None:
        return Path(home) / ".config" / "post-ip"
    raise RuntimeError("Neither $XDG_CONFIG_HOME nor $HOME is set. Exiting.")

# }}}


# get_cache_home_fp() {{{

_cache_home: Path | None = None
def get_cache_home_fp() -> Path:
    global _cache_home
    if _cache_home is None:
        _cache_home = _get_cache_home_fp()
        _cache_home.mkdir(parents=True, exist_ok=True)
    return _cache_home


def _get_cache_home_fp() -> Path:
    if (cache_home := os.environ.get("XDG_CACHE_HOME", None)) is not None:
        return Path(cache_home) / "post-ip"
    if (home := os.environ.get("HOME", None)) is not None:
        return Path(home) / ".cache" / "post-ip"
    raise RuntimeError("Neither $XDG_CACHE_HOME nor $HOME is set. Exiting.")

# }}}


# get_scopes_fp() {{{

_scopes_fp: Path | None = None
def get_scopes_fp() -> Path:
    global _scopes_fp
    if _scopes_fp is None:
        _scopes_fp = Path(__file__).parent / "scopes.list"
    return _scopes_fp

# }}}


# get_oauth_token_fp() {{{

_token_path: Path | None = None
def get_oauth_token_fp() -> Path:
    global _token_path
    if _token_path is None:
        _token_path = _get_oauth_token_fp()
    return _token_path


def _get_oauth_token_fp() -> Path:
    if (token_path := os.environ.get("POSTIP_TOKEN")) is not None:
        return Path(token_path)
    return get_cache_home_fp() / "token.json"

# }}}


# get_last_ip_fp() {{{

_last_ip: Path | None = None
def get_last_ip_fp() -> Path:
    global _last_ip
    if _last_ip is None:
        _last_ip = _get_last_ip_fp()
    return _last_ip


def _get_last_ip_fp() -> Path:
    if (token_path := os.environ.get("POSTIP_LASTIP")) is not None:
        return Path(token_path)
    return get_cache_home_fp() / "last_ip"

# }}}


# get_credentials_fp() {{{

_credentials_fp: Path | None = None
def get_credentials_fp() -> Path:
    global _credentials_fp
    if _credentials_fp is None:
        _credentials_fp = _get_credentials_fp()
    return _credentials_fp


def _get_credentials_fp() -> Path:
    if (credentials_fp := os.environ.get("POSTIP_CREDENTIALS")) is not None:
        return Path(credentials_fp)
    return get_config_home_fp() / "credentials.json"

# }}}
