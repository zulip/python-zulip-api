from ctypes import (
    CDLL,
    CFUNCTYPE,
    POINTER,
    Structure,
    Union,
    c_char,
    c_char_p,
    c_int,
    c_long,
    c_uint,
    c_uint8,
    c_uint16,
    c_uint32,
    c_ushort,
    c_void_p,
)

from typing_extensions import override

libc = CDLL("libc.so.6")
com_err = CDLL("libcom_err.so.2")
libzephyr = CDLL("libzephyr.so.4")


# --- glibc/bits/sockaddr.h ---

sa_family_t = c_ushort


# --- glibc/sysdeps/unix/sysv/linux/bits/socket.h ---


class sockaddr(Structure):  # noqa: N801
    _fields_ = (
        ("sa_family", sa_family_t),
        ("sa_data", c_char * 14),
    )


# --- glibc/inet/netinet/in.h ---

in_port_t = c_uint16
in_addr_t = c_uint32


class in_addr(Structure):  # noqa: N801
    _fields_ = (("s_addr", in_addr_t),)


class sockaddr_in(Structure):  # noqa: N801
    _fields_ = (
        ("sin_family", sa_family_t),
        ("sin_port", in_port_t),
        ("sin_addr", in_addr),
        ("sin_zero", c_uint8 * 8),
    )


class in6_addr(Structure):  # noqa: N801
    _fields_ = (("s6_addr", c_uint8 * 16),)


class sockaddr_in6(Structure):  # noqa: N801
    _fields_ = (
        ("sin6_family", sa_family_t),
        ("sin6_port", in_port_t),
        ("sin6_flowinfo", c_uint32),
        ("sin6_addr", in6_addr),
        ("sin6_scope_id", c_uint32),
    )


# --- glibc/stdlib/stdlib.h ---

free = CFUNCTYPE(None, c_void_p)(("free", libc))


# --- e2fsprogs/lib/et/com_err.h ---

error_message = CFUNCTYPE(c_char_p, c_long)(("error_message", com_err))


# --- zephyr/h/zephyr/zephyr.h ---

Z_MAXOTHERFIELDS = 10

ZNotice_Kind_t = c_int


class _ZTimeval(Structure):
    _fields_ = (
        ("tv_sec", c_int),
        ("tv_usec", c_int),
    )


class ZUnique_Id_t(Structure):  # noqa: N801
    _fields_ = (
        ("zuid_addr", in_addr),
        ("tv", _ZTimeval),
    )


ZChecksum_t = c_uint


class _ZSenderSockaddr(Union):
    _fields_ = (
        ("sa", sockaddr),
        ("ip4", sockaddr_in),
        ("ip6", sockaddr_in6),
    )


class ZNotice_t(Structure):  # noqa: N801
    _fields_ = (
        ("z_packet", c_char_p),
        ("z_version", c_char_p),
        ("z_kind", ZNotice_Kind_t),
        ("z_uid", ZUnique_Id_t),
        ("z_sender_sockaddr", _ZSenderSockaddr),
        ("z_time", _ZTimeval),
        ("z_port", c_ushort),
        ("z_charset", c_ushort),
        ("z_auth", c_int),
        ("z_checked_auth", c_int),
        ("z_authent_len", c_int),
        ("z_ascii_authent", c_char_p),
        ("z_class", c_char_p),
        ("z_class_inst", c_char_p),
        ("z_opcode", c_char_p),
        ("z_sender", c_char_p),
        ("z_recipient", c_char_p),
        ("z_default_format", c_char_p),
        ("z_multinotice", c_char_p),
        ("z_multiuid", ZUnique_Id_t),
        ("z_checksum", ZChecksum_t),
        ("z_ascii_checksum", c_char_p),
        ("z_num_other_fields", c_int),
        ("z_other_fields", c_char_p * Z_MAXOTHERFIELDS),
        ("z_message", POINTER(c_char)),
        ("z_message_len", c_int),
        ("z_num_hdr_fields", c_uint),
        ("z_hdr_fields", POINTER(c_char_p)),
    )


class ZSubscription_t(Structure):  # noqa: N801
    _fields_ = (
        ("zsub_recipient", c_char_p),
        ("zsub_class", c_char_p),
        ("zsub_classinst", c_char_p),
    )


Code_t = c_int

ZInitialize = CFUNCTYPE(Code_t)(("ZInitialize", libzephyr))
ZRetrieveSubscriptions = CFUNCTYPE(Code_t, c_ushort, POINTER(c_int))(
    ("ZRetrieveSubscriptions", libzephyr)
)
ZGetSubscriptions = CFUNCTYPE(Code_t, POINTER(ZSubscription_t), POINTER(c_int))(
    ("ZGetSubscriptions", libzephyr)
)
ZOpenPort = CFUNCTYPE(Code_t, POINTER(c_ushort))(("ZOpenPort", libzephyr))
ZFlushSubscriptions = CFUNCTYPE(Code_t)(("ZFlushSubscriptions", libzephyr))
ZFreeNotice = CFUNCTYPE(Code_t, POINTER(ZNotice_t))(("ZFreeNotice", libzephyr))
ZSubscribeTo = CFUNCTYPE(Code_t, POINTER(ZSubscription_t), c_int, c_uint)(
    ("ZSubscribeTo", libzephyr)
)
ZCancelSubscriptions = CFUNCTYPE(Code_t, c_uint)(("ZCancelSubscriptions", libzephyr))
ZPending = CFUNCTYPE(c_int)(("ZPending", libzephyr))
ZReceiveNotice = CFUNCTYPE(Code_t, POINTER(ZNotice_t), POINTER(sockaddr_in))(
    ("ZReceiveNotice", libzephyr)
)
ZDumpSession = CFUNCTYPE(Code_t, POINTER(POINTER(c_char)), POINTER(c_int))(
    ("ZDumpSession", libzephyr)
)
ZLoadSession = CFUNCTYPE(Code_t, POINTER(c_char), c_int)(("ZLoadSession", libzephyr))
ZGetFD = CFUNCTYPE(c_int)(("ZGetFD", libzephyr))

ZERR_NONE = 0


# --- zephyr/lib/zephyr_err.et ---

ERROR_TABLE_BASE_zeph = -772103680
ZERR_SERVNAK = ERROR_TABLE_BASE_zeph + 16


# --- convenience helpers ---


class ZephyrError(Exception):
    def __init__(self, code: int) -> None:
        self.code = code

    @override
    def __str__(self) -> str:
        return error_message(self.code).decode()


def check(code: int) -> None:
    if code != ZERR_NONE:
        raise ZephyrError(code)
