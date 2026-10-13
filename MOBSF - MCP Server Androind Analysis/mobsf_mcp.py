
#!/usr/bin/env python3

import os
import json
import urllib.request
import urllib.error
import uuid
from pathlib import Path
from urllib.parse import urlencode

from fastmcp import FastMCP

mcp = FastMCP("MobSF Security Server")

MOBSF_URL = os.getenv(
    "MOBSF_URL", "http://127.0.0.1:8000"
).rstrip("/")

MOBSF_API_KEY = os.getenv("MOBSF_API_KEY", "")
MAX_UPLOAD_SIZE = 200 * 1024 * 1024
TIMEOUT = 180


def mobsf_request(endpoint, fields=None, file_path=None):
    """Make an authenticated request to the MobSF API."""

    if not MOBSF_API_KEY:
        raise RuntimeError(
            "MOBSF_API_KEY is not configured."
        )

    url = f"{MOBSF_URL}/api/v1/{endpoint.lstrip('/')}"
    headers = {"Authorization": MOBSF_API_KEY}
    data = None

    if file_path:
        path = Path(file_path).expanduser().resolve()

        if not path.is_file():
            raise FileNotFoundError(str(path))

        if path.stat().st_size > MAX_UPLOAD_SIZE:
            raise ValueError("File exceeds the 200 MB limit.")

        boundary = uuid.uuid4().hex

        headers["Content-Type"] = (
            f"multipart/form-data; boundary={boundary}"
        )

        with path.open("rb") as file:
            contents = file.read(MAX_UPLOAD_SIZE + 1)

        if len(contents) > MAX_UPLOAD_SIZE:
            raise ValueError("File exceeds the 200 MB limit.")

        data = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; '
            f'filename="{path.name}"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n"
        ).encode() + contents + f"\r\n--{boundary}--\r\n".encode()

    elif fields is not None:
        data = urlencode(fields).encode()
        headers["Content-Type"] = (
            "application/x-www-form-urlencoded"
        )

    request = urllib.request.Request(
        url, data=data, headers=headers, method="POST"
    )

    try:
        with urllib.request.urlopen(
            request, timeout=TIMEOUT
        ) as response:
            body = response.read()

            if response.headers.get_content_type() == "application/pdf":
                return body

            return json.loads(body.decode("utf-8"))

    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"MobSF HTTP {exc.code}: {detail[:1500]}"
        ) from exc

    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Cannot connect to MobSF at {MOBSF_URL}: "
            f"{exc.reason}"
        ) from exc


@mcp.tool()
def mobsf_status() -> dict:
    """Check whether the MobSF web service is reachable."""

    try:
        with urllib.request.urlopen(
            MOBSF_URL, timeout=10
        ) as response:
            return {
                "reachable": True,
                "http_status": response.status,
                "url": MOBSF_URL,
                "api_key_configured": bool(MOBSF_API_KEY),
            }
    except Exception as exc:
        return {
            "reachable": False,
            "url": MOBSF_URL,
            "error": str(exc),
        }


@mcp.tool()
def mobsf_upload_and_scan(file_path: str) -> dict:
    """
    Upload an authorized APK or supported file to MobSF
    and initiate static analysis.
    """

    path = Path(file_path).expanduser().resolve()

    if not path.is_file():
        raise FileNotFoundError(str(path))

    uploaded = mobsf_request(
        "upload", file_path=str(path)
    )

    if not isinstance(uploaded, dict) or not uploaded.get("hash"):
        return {
            "upload_response": uploaded,
            "scan_started": False,
        }

    scan_hash = uploaded["hash"]

    result = mobsf_request(
        "scan",
        {
            "hash": scan_hash,
            "re_scan": "0",
        },
    )

    return {
        "filename": path.name,
        "hash": scan_hash,
        "upload": uploaded,
        "scan_result": result,
    }


@mcp.tool()
def mobsf_get_json_report(scan_hash: str) -> dict:
    """Retrieve the full MobSF JSON report for a scan hash."""

    return mobsf_request(
        "report_json", {"hash": scan_hash}
    )


@mcp.tool()
def mobsf_search(query: str) -> dict:
    """Search MobSF for existing scans by filename, package or hash."""

    return mobsf_request(
        "search", {"query": query}
    )


@mcp.tool()
def mobsf_recent_scans() -> dict:
    """List recent scans recorded by MobSF."""

    return mobsf_request("scans", {})


@mcp.tool()
def mobsf_scan_logs(scan_hash: str) -> dict:
    """Retrieve MobSF scan logs for a scan hash."""

    return mobsf_request(
        "scan_logs", {"hash": scan_hash}
    )


@mcp.tool()
def mobsf_download_pdf_report(scan_hash: str) -> dict:
    """Download a PDF report into the local reports directory."""

    output_dir = Path(
        os.getenv(
            "MOBSF_REPORT_DIR",
            "/home/kali/mcp/android/mobsf_reports",
        )
    ).expanduser().resolve()

    output_dir.mkdir(parents=True, exist_ok=True)

    # Use a validated hash in the output filename.
    if not scan_hash or any(
        c not in "0123456789abcdefABCDEF-" for c in scan_hash
    ):
        raise ValueError("Invalid scan hash.")

    pdf = mobsf_request(
        "download_pdf", {"hash": scan_hash}
    )

    if not isinstance(pdf, bytes) or not pdf.startswith(b"%PDF"):
        raise RuntimeError("MobSF did not return a valid PDF.")

    output_path = output_dir / f"{scan_hash}.pdf"
    output_path.write_bytes(pdf)

    return {
        "saved": True,
        "path": str(output_path),
        "size_bytes": len(pdf),
    }


if __name__ == "__main__":
    mcp.run()
