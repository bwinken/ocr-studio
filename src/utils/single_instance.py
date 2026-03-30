import ctypes


def ensure_single_instance(mutex_name: str):
    """Create a Windows named mutex. Returns handle if first instance, None otherwise."""
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.CreateMutexW(None, False, mutex_name)
    ERROR_ALREADY_EXISTS = 183
    if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        kernel32.CloseHandle(handle)
        return None
    return handle
