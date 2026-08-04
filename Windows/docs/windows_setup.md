# Windows Credential Provider — Setup Guide

## Overview

FaceLock can integrate with the Windows login screen via a custom
Credential Provider. This requires two components:

1. **C++ COM DLL** — Registered as a Windows Credential Provider.
2. **Python Bridge** (`credential_bridge.py`) — Called by the DLL to verify
   credentials against the FaceLock auth service.

## Current Status

> **Stub Implementation**: The Python bridge is functional and can be tested
> against the FaceLock auth service running on WSL or Linux. The COM DLL
> must be built in a Windows development environment with Visual Studio.

## Architecture

```text
Windows Login Screen
        │
   Credential Provider DLL (COM)
        │
   credential_bridge.py
        │
   FaceLock Auth Service Socket
        │
   Core Authentication Engine
```

## Testing the Bridge (WSL / Linux)

1. Start the auth service:
   ```bash
   python3 Service/main.py
   ```

2. Test the bridge:
   ```bash
   python3 Windows/credential_provider/credential_bridge.py <username> <password>
   echo $?  # 0 = success, 1 = failure
   ```

## Future Development

- Build the C++ COM Credential Provider DLL using the Windows SDK.
- Register the DLL with `regsvr32`.
- The DLL spawns `credential_bridge.py` as a child process.
