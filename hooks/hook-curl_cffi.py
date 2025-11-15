"""PyInstaller hook for curl_cffi - ensures all native libraries are included"""

from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs

# Collect everything from curl_cffi
datas, binaries, hiddenimports = collect_all('curl_cffi')

# Ensure all DLLs are included
binaries += collect_dynamic_libs('curl_cffi')

# Add all submodules
hiddenimports += [
    'curl_cffi',
    'curl_cffi.requests',
    'curl_cffi.const',
    'curl_cffi.curl',
    'curl_cffi.aio',
    '_cffi_backend',
]
