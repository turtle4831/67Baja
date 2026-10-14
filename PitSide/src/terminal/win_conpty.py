"""Windows ConPTY. ponytail: fixed 100x24, no resize. Needs Windows 10 1809+.
Upgrade path is pywinpty if a Windows build rejects the attribute list."""

import ctypes
import os

# Fixed-width types. wintypes.DWORD is c_ulong, which is 8 bytes on Linux and
# 4 on Windows, so the layout check below would not match the Win32 ABI.
_DWORD = ctypes.c_uint32
_WORD = ctypes.c_uint16
_SHORT = ctypes.c_int16
_BOOL = ctypes.c_int32
_HANDLE = ctypes.c_void_p

PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE = 0x00020016
EXTENDED_STARTUPINFO_PRESENT = 0x00080000
HANDLE_FLAG_INHERIT = 0x00000001
STILL_ACTIVE = 259

_k32 = None


class COORD(ctypes.Structure):
    _fields_ = [("X", _SHORT), ("Y", _SHORT)]


class SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("nLength", _DWORD),
        ("lpSecurityDescriptor", _HANDLE),
        ("bInheritHandle", _BOOL),
    ]


class STARTUPINFOW(ctypes.Structure):
    _fields_ = [
        ("cb", _DWORD),
        ("lpReserved", ctypes.c_wchar_p),
        ("lpDesktop", ctypes.c_wchar_p),
        ("lpTitle", ctypes.c_wchar_p),
        ("dwX", _DWORD),
        ("dwY", _DWORD),
        ("dwXSize", _DWORD),
        ("dwYSize", _DWORD),
        ("dwXCountChars", _DWORD),
        ("dwYCountChars", _DWORD),
        ("dwFillAttribute", _DWORD),
        ("dwFlags", _DWORD),
        ("wShowWindow", _WORD),
        ("cbReserved2", _WORD),
        ("lpReserved2", ctypes.c_void_p),
        ("hStdInput", _HANDLE),
        ("hStdOutput", _HANDLE),
        ("hStdError", _HANDLE),
    ]


class STARTUPINFOEXW(ctypes.Structure):
    _fields_ = [("StartupInfo", STARTUPINFOW), ("lpAttributeList", ctypes.c_void_p)]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("hProcess", _HANDLE),
        ("hThread", _HANDLE),
        ("dwProcessId", _DWORD),
        ("dwThreadId", _DWORD),
    ]


def _self_check() -> None:
    assert ctypes.sizeof(COORD) == 4
    assert PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE == 0x20016
    ptr = ctypes.sizeof(ctypes.c_void_p)
    if ptr == 8:
        assert ctypes.sizeof(STARTUPINFOW) == 104
        assert ctypes.sizeof(STARTUPINFOEXW) == 112
        assert ctypes.sizeof(SECURITY_ATTRIBUTES) == 24
        assert ctypes.sizeof(PROCESS_INFORMATION) == 24
    else:
        assert ctypes.sizeof(STARTUPINFOW) == 68
        assert ctypes.sizeof(STARTUPINFOEXW) == 72
        assert ctypes.sizeof(SECURITY_ATTRIBUTES) == 12
        assert ctypes.sizeof(PROCESS_INFORMATION) == 16


_self_check()


def _kernel32():
    global _k32
    if _k32 is not None:
        return _k32
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreatePipe.argtypes = [
        ctypes.POINTER(_HANDLE),
        ctypes.POINTER(_HANDLE),
        ctypes.POINTER(SECURITY_ATTRIBUTES),
        _DWORD,
    ]
    k.CreatePipe.restype = _BOOL
    k.SetHandleInformation.argtypes = [_HANDLE, _DWORD, _DWORD]
    k.SetHandleInformation.restype = _BOOL
    k.CloseHandle.argtypes = [_HANDLE]
    k.CloseHandle.restype = _BOOL
    k.CreatePseudoConsole.argtypes = [
        COORD,
        _HANDLE,
        _HANDLE,
        _DWORD,
        ctypes.POINTER(_HANDLE),
    ]
    k.CreatePseudoConsole.restype = ctypes.c_long
    k.ClosePseudoConsole.argtypes = [_HANDLE]
    k.ClosePseudoConsole.restype = None
    k.InitializeProcThreadAttributeList.argtypes = [
        ctypes.c_void_p,
        _DWORD,
        _DWORD,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    k.InitializeProcThreadAttributeList.restype = _BOOL
    k.UpdateProcThreadAttribute.argtypes = [
        ctypes.c_void_p,
        _DWORD,
        ctypes.c_size_t,
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_void_p,
        ctypes.c_void_p,
    ]
    k.UpdateProcThreadAttribute.restype = _BOOL
    k.DeleteProcThreadAttributeList.argtypes = [ctypes.c_void_p]
    k.DeleteProcThreadAttributeList.restype = None
    k.CreateProcessW.argtypes = [
        ctypes.c_wchar_p,
        ctypes.c_wchar_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        _BOOL,
        _DWORD,
        ctypes.c_void_p,
        ctypes.c_wchar_p,
        ctypes.POINTER(STARTUPINFOEXW),
        ctypes.POINTER(PROCESS_INFORMATION),
    ]
    k.CreateProcessW.restype = _BOOL
    k.TerminateProcess.argtypes = [_HANDLE, _DWORD]
    k.TerminateProcess.restype = _BOOL
    k.GetExitCodeProcess.argtypes = [_HANDLE, ctypes.POINTER(_DWORD)]
    k.GetExitCodeProcess.restype = _BOOL
    _k32 = k
    return k


def _close_handles(k, *handles) -> None:
    for handle in handles:
        if handle is not None and handle.value:
            k.CloseHandle(handle)


def _pipes(k):
    sa = SECURITY_ATTRIBUTES()
    sa.nLength = ctypes.sizeof(sa)
    sa.bInheritHandle = True
    in_read, in_write = _HANDLE(), _HANDLE()
    out_read, out_write = _HANDLE(), _HANDLE()
    if not k.CreatePipe(
        ctypes.byref(in_read), ctypes.byref(in_write), ctypes.byref(sa), 0
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    if not k.CreatePipe(ctypes.byref(out_read), ctypes.byref(out_write), ctypes.byref(sa), 0):
        _close_handles(k, in_read, in_write)
        raise ctypes.WinError(ctypes.get_last_error())
    k.SetHandleInformation(in_write, HANDLE_FLAG_INHERIT, 0)
    k.SetHandleInformation(out_read, HANDLE_FLAG_INHERIT, 0)
    return in_read, in_write, out_read, out_write


def _attribute_list(k, hpc):
    # First call only reports the byte count. Failure here is expected.
    size = ctypes.c_size_t()
    k.InitializeProcThreadAttributeList(None, 1, 0, ctypes.byref(size))
    buf = (ctypes.c_char * size.value)()
    if not k.InitializeProcThreadAttributeList(buf, 1, 0, ctypes.byref(size)):
        raise ctypes.WinError(ctypes.get_last_error())
    # Pass the HPCON itself, matching the Microsoft ConPTY sample.
    if not k.UpdateProcThreadAttribute(
        buf,
        0,
        PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE,
        hpc,
        ctypes.sizeof(_HANDLE),
        None,
        None,
    ):
        err = ctypes.WinError(ctypes.get_last_error())
        k.DeleteProcThreadAttributeList(buf)
        raise err
    return buf


def _shell_command() -> str:
    shell = os.environ.get("COMSPEC") or "cmd.exe"
    return f'"{shell}"' if " " in shell else shell


def _fd(msvcrt, handle, mode: int) -> int:
    fd = msvcrt.open_osfhandle(handle.value, mode)
    if fd == -1:
        raise OSError("open_osfhandle failed")
    return fd


class ConPty:
    def __init__(self, k, hpc, process, thread, read_fd: int, write_fd: int):
        self._k = k
        self._hpc = hpc
        self._process = process
        self._thread = thread
        self._read_fd = read_fd
        self._write_fd = write_fd
        self._closed = False

    def read(self) -> bytes:
        fd = self._read_fd
        if fd is None:
            return b""
        try:
            return os.read(fd, 4096)
        except OSError:
            return b""

    def write(self, data: bytes) -> None:
        fd = self._write_fd
        if fd is None:
            return
        try:
            os.write(fd, data)
        except OSError:
            pass

    def alive(self) -> bool:
        if self._closed or not self._process:
            return False
        code = _DWORD()
        if not self._k.GetExitCodeProcess(self._process, ctypes.byref(code)):
            return False
        return code.value == STILL_ACTIVE

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._hpc:
            self._k.ClosePseudoConsole(self._hpc)
            self._hpc = None
        if self._process:
            self._k.TerminateProcess(self._process, 1)
            self._k.CloseHandle(self._process)
            self._k.CloseHandle(self._thread)
            self._process = None
        for fd in (self._read_fd, self._write_fd):
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
        self._read_fd = None
        self._write_fd = None


def open_console(cols: int = 100, rows: int = 24) -> ConPty:
    import msvcrt

    k = None
    in_read = in_write = out_read = out_write = None
    hpc = None
    try:
        k = _kernel32()
        if not hasattr(k, "CreatePseudoConsole"):
            raise OSError("ConPTY requires Windows 10 version 1809 or newer")
        in_read, in_write, out_read, out_write = _pipes(k)
        hpc = _HANDLE()
        hr = k.CreatePseudoConsole(
            COORD(cols, rows), in_read, out_write, 0, ctypes.byref(hpc)
        )
        _close_handles(k, in_read, out_write)
        in_read = out_write = None
        if hr < 0:
            hpc = None
            raise OSError(f"CreatePseudoConsole failed ({hr:#x})")
        attr = _attribute_list(k, hpc)
        try:
            command = ctypes.create_unicode_buffer(_shell_command())
            pi = PROCESS_INFORMATION()
            si = STARTUPINFOEXW()
            si.StartupInfo.cb = ctypes.sizeof(STARTUPINFOEXW)
            si.lpAttributeList = ctypes.addressof(attr)
            if not k.CreateProcessW(
                None,
                command,
                None,
                None,
                False,
                EXTENDED_STARTUPINFO_PRESENT,
                None,
                None,
                ctypes.byref(si),
                ctypes.byref(pi),
            ):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            k.DeleteProcThreadAttributeList(attr)
        read_fd = _fd(msvcrt, out_read, os.O_RDONLY | os.O_BINARY)
        out_read = None
        try:
            write_fd = _fd(msvcrt, in_write, os.O_WRONLY | os.O_BINARY)
        except Exception:
            os.close(read_fd)
            raise
        in_write = None
        session = ConPty(k, hpc, pi.hProcess, pi.hThread, read_fd, write_fd)
        hpc = None
        return session
    except Exception:
        if k is not None and hpc is not None and hpc.value:
            k.ClosePseudoConsole(hpc)
        if k is not None:
            _close_handles(k, in_read, in_write, out_read, out_write)
        raise
