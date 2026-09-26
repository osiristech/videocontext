"""Optional network route shared by YouTube extractors."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlsplit


def configured_proxy() -> str | None:
    """Read a proxy URL without exposing it in command-line arguments."""
    proxy_file = os.environ.get("VIDEOCONTEXT_PROXY_FILE")
    if proxy_file:
        try:
            proxy = Path(proxy_file).expanduser().read_text(encoding="utf-8").strip()
        except (OSError, UnicodeError) as error:
            raise RuntimeError("Could not read VIDEOCONTEXT_PROXY_FILE") from error
    else:
        proxy = os.environ.get("VIDEOCONTEXT_PROXY", "").strip()

    if not proxy:
        if proxy_file:
            raise RuntimeError("VIDEOCONTEXT_PROXY_FILE is empty")
        return None

    try:
        parsed = urlsplit(proxy)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as error:
        raise RuntimeError("Invalid VideoContext proxy URL") from error
    if parsed.scheme not in {"http", "https", "socks4", "socks5", "socks5h"} or not hostname:
        raise RuntimeError("VideoContext proxy must be an HTTP, HTTPS, SOCKS4, or SOCKS5 URL")
    if port is None and ":" in parsed.netloc.rsplit("@", 1)[-1] and not parsed.netloc.endswith("]"):
        raise RuntimeError("Invalid VideoContext proxy port")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise RuntimeError("VideoContext proxy URL must not contain a path, query, or fragment")

    if parsed.scheme.startswith("socks"):
        try:
            import socks  # noqa: F401
        except ImportError as error:
            raise RuntimeError(
                "SOCKS proxy support requires the 'proxy' extra: pip install videocontext[proxy]"
            ) from error
    return proxy


class _QuietYtDlpLogger:
    """Keep proxy credentials out of yt-dlp diagnostics."""

    def debug(self, message: str) -> None:
        pass

    def warning(self, message: str) -> None:
        pass

    def error(self, message: str) -> None:
        pass


def yt_dlp_proxy_options() -> dict:
    proxy = configured_proxy()
    if proxy is None:
        return {}
    return {"proxy": proxy, "logger": _QuietYtDlpLogger()}
