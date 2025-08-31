import asyncio

async def ir_send(protocol: str, hex_code: str, device_path: str) -> tuple[bool, str]:
    proc = await asyncio.create_subprocess_exec(
        "ir-ctl",
        "--device",
        device_path,
        "-S",
        f"{protocol}:{hex_code}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    ok = proc.returncode == 0
    return ok, (
        out.decode().strip() if ok else err.decode().strip() or out.decode().strip()
    )