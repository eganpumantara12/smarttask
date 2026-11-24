import socket
import smtplib


def _resolve_ipv4(host: str) -> str:
    infos = socket.getaddrinfo(host, None, family=socket.AF_INET, type=socket.SOCK_STREAM)
    return infos[0][4][0] if infos else host


def _send_via_smtp(host: str, port: int, user: str, password: str, raw_message: str) -> None:
    target_host = _resolve_ipv4(host)
    if port == 465:
        with smtplib.SMTP_SSL(target_host, port, timeout=15) as server:
            server.ehlo(host)
            server.login(user, password)
            server.sendmail(user, to_addrs, raw_message)
    else:
        with smtplib.SMTP(target_host, port, timeout=15) as server:
            server.ehlo(host)
            server.starttls()
            server.ehlo(host)
            server.login(user, password)
            server.sendmail(user, to_addrs, raw_message)
