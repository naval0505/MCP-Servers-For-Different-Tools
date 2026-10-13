#!/usr/bin/env python3
"""
MobSF MCP server for Android application security (static analysis).

Environment:
  MOBSF_URL          MobSF base URL (default http://127.0.0.1:8000)
  MOBSF_API_KEY      MobSF REST API key (required)
  MOBSF_UPLOAD_ROOT  Directory allowed for uploads (default ~/mobsf_samples)
  MOBSF_REPORT_DIR   Directory for PDF reports (default ~/mobsf_reports)

Run directly with system Python; no virtual environment is required.
"""

import json
import logging
import os
import re
import secrets
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("mobsf-mcp")

mcp = FastMCP("MobSF Android AppSec Server")

MOBSF_URL = os.getenv("MOBSF_URL", "http://127.0.0.1:8000").rstrip("/")
MOBSF_API_KEY = os.getenv("MOBSF_API_KEY", "")
UPLOAD_ROOT = Path(
    os.getenv("MOBSF_UPLOAD_ROOT", "~/mobsf_samples")
).expanduser().resolve()
REPORT_DIR = Path(
    os.getenv("MOBSF_REPORT_DIR", "~/mobsf_reports")
).expanduser().resolve()

ALLOWED_EXTENSIONS = {".apk", ".aab", ".zip"}
MAX_UPLOAD_SIZE = 200 * 1024 * 1024
HTTP_TIMEOUT = 60
SCAN_TIMEOUT = 900
HASH_RE = re.compile(r"[0-9a-fA-F]{32}")


def _validate_hash(scan_hash: str) -> str:
    """Validate a MobSF scan hash before passing it to the API."""
    if not isinstance(scan_hash, str) or not HASH_RE.fullmatch(scan_hash):
        raise ValueError("scan_hash must be a 32-character hexadecimal MobSF hash.")
    return scan_hash.lower()


def _validate_upload(file_path: str) -> Path:
    """Ensure the requested upload is a permitted file under UPLOAD_ROOT."""
    if not file_path or not isinstance(file_path, str):
        raise ValueError("file_path must be a non-empty path.")

    path = Path(file_path).expanduser()
    if not path.is_absolute():
        path = UPLOAD_ROOT / path
    path = path.resolve()

    if not path.is_relative_to(UPLOAD_ROOT):
        raise PermissionError(f"Uploads are restricted to {UPLOAD_ROOT}.")

    if not path.is_file():
        raise FileNotFoundError(str(path))

    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{path.suffix}'. "
            f"Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    if path.stat().st_size > MAX_UPLOAD_SIZE:
        raise ValueError("File exceeds the 200 MB upload limit.")

    return path


def _multipart(path: Path) -> tuple[bytes, str]:
    """Build a multipart upload body with a sanitized filename."""
    boundary = secrets.token_hex(16)
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", path.name)
    head = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{safe_name}"\r\n'
        "Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8")
    tail = f"\r\n--{boundary}--\r\n".encode("utf-8")

    with path.open("rb") as handle:
        contents = handle.read(MAX_UPLOAD_SIZE + 1)
    if len(contents) > MAX_UPLOAD_SIZE:
        raise ValueError("File exceeds the 200 MB upload limit.")

    return head + contents + tail, f"multipart/form-data; boundary={boundary}"


def _api(
    endpoint: str,
    fields: dict[str, str] | None = None,
    file_path: Path | None = None,
    timeout: int = HTTP_TIMEOUT,
) -> Any:
    """Call a MobSF API endpoint and parse its JSON or PDF response."""
    if not MOBSF_API_KEY:
        raise RuntimeError(
            "MOBSF_API_KEY is not set. Configure it in the MCP server environment."
        )

    url = f"{MOBSF_URL}/api/v1/{endpoint.lstrip('/')}"
    headers = {
        "Authorization": MOBSF_API_KEY,
        "Accept": "application/json, application/pdf",
    }

    if file_path is not None:
        body, content_type = _multipart(file_path)
        headers["Content-Type"] = content_type
    elif fields is not None:
        body = urllib.parse.urlencode(fields).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    else:
        body = None

    request = urllib.request.Request(
        url, data=body, headers=headers, method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get_content_type()
            raw = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1500]
        raise RuntimeError(
            f"MobSF HTTP {exc.code} on '{endpoint}': {detail}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Cannot reach MobSF at {MOBSF_URL}: {exc.reason}"
        ) from exc
    except TimeoutError as exc:
        raise RuntimeError(f"MobSF request timed out on '{endpoint}'.") from exc

    if content_type == "application/pdf" or raw.startswith(b"%PDF"):
        return raw

    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"MobSF returned a non-JSON response for '{endpoint}'."
        ) from exc


SEVERITY_MAP = {
    "high": "high",
    "warning": "medium",
    "medium": "medium",
    "low": "low",
    "info": "info",
    "secure": "secure",
    "critical": "critical",
}
SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "info": 4,
    "secure": 5,
}


def _norm_sev(value: Any) -> str:
    return SEVERITY_MAP.get(str(value or "").lower(), "info")


def _manifest_findings(report: dict) -> list[dict]:
    items = (report.get("manifest_analysis") or {}).get("manifest_findings", [])
    if not isinstance(items, list):
        return []

    findings = []
    for item in items:
        if isinstance(item, dict):
            findings.append({
                "source": "manifest",
                "severity": _norm_sev(item.get("severity")),
                "title": item.get("title") or item.get("rule"),
                "detail": item.get("description"),
                "component": item.get("name"),
            })
    return findings


def _code_findings(report: dict) -> list[dict]:
    code = report.get("code_analysis") or {}
    if not isinstance(code, dict):
        return []

    rules = code.get("findings", code)
    if not isinstance(rules, dict):
        return []

    findings = []
    for rule_id, info in rules.items():
        if rule_id == "summary" or not isinstance(info, dict):
            continue
        metadata = info.get("metadata") or {}
        files = info.get("files") or []
        if not isinstance(metadata, dict):
            metadata = {}
        if not isinstance(files, list):
            files = []

        findings.append({
            "source": "code",
            "rule": rule_id,
            "severity": _norm_sev(metadata.get("severity")),
            "title": metadata.get("description", rule_id),
            "cwe": metadata.get("cwe"),
            "owasp_mobile": metadata.get("owasp-mobile"),
            "file_count": len(files),
            "files": [
                item.get("file_path", item) if isinstance(item, dict) else item
                for item in files[:10]
            ],
        })
    return findings


def _certificate_findings(report: dict) -> list[dict]:
    section = report.get("certificate_analysis") or {}
    items = section.get("certificate_findings", []) if isinstance(section, dict) else []
    if not isinstance(items, list):
        return []

    findings = []
    for item in items:
        if isinstance(item, dict):
            severity = item.get("severity")
            title = item.get("title")
            detail = item.get("description")
        elif isinstance(item, (list, tuple)) and len(item) >= 3:
            severity, title, detail = item[0], item[1], item[2]
        else:
            continue

        findings.append({
            "source": "certificate",
            "severity": _norm_sev(severity),
            "title": title,
            "detail": detail,
        })
    return findings


def _summarize(report: dict) -> dict:
    """Create a compact triage summary from a MobSF JSON report."""
    findings = (
        _manifest_findings(report)
        + _code_findings(report)
        + _certificate_findings(report)
    )
    findings.sort(
        key=lambda item: SEVERITY_ORDER.get(item["severity"], 99)
    )

    counts: dict[str, int] = {}
    for finding in findings:
        severity = finding["severity"]
        counts[severity] = counts.get(severity, 0) + 1

    permissions = report.get("permissions") or {}
    dangerous_permissions = []
    if isinstance(permissions, dict):
        dangerous_permissions = sorted(
            name for name, info in permissions.items()
            if isinstance(info, dict)
            and str(info.get("status", "")).lower() == "dangerous"
        )

    trackers_section = report.get("trackers") or {}
    trackers = (
        trackers_section.get("detected_trackers", [])
        if isinstance(trackers_section, dict)
        else []
    )
    secrets_section = report.get("secrets") or []
    if isinstance(secrets_section, dict):
        secret_count = len(secrets_section)
        secret_sample = list(secrets_section.values())[:20]
    elif isinstance(secrets_section, list):
        secret_count = len(secrets_section)
        secret_sample = secrets_section[:20]
    else:
        secret_count = 0
        secret_sample = []

    return {
        "app_name": report.get("app_name"),
        "package_name": report.get("package_name"),
        "version_name": report.get("version_name"),
        "version_code": report.get("version_code"),
        "min_sdk": report.get("min_sdk"),
        "target_sdk": report.get("target_sdk"),
        "finding_counts": counts,
        "findings": findings[:200],
        "findings_truncated": len(findings) > 200,
        "dangerous_permissions": dangerous_permissions,
        "secrets_count": secret_count,
        "secrets_sample": secret_sample,
        "trackers_count": trackers if isinstance(trackers, int) else (
            len(trackers) if isinstance(trackers, (list, dict)) else 0
        ),
    }


@mcp.tool()
def mobsf_status() -> dict:
    """Check MobSF reachability and whether the API key is configured."""
    try:
        with urllib.request.urlopen(MOBSF_URL, timeout=10) as response:
            return {
                "reachable": True,
                "http_status": response.status,
                "url": MOBSF_URL,
                "api_key_configured": bool(MOBSF_API_KEY),
                "upload_root": str(UPLOAD_ROOT),
            }
    except Exception as exc:
        return {
            "reachable": False,
            "url": MOBSF_URL,
            "api_key_configured": bool(MOBSF_API_KEY),
            "error": str(exc),
        }


@mcp.tool()
def mobsf_upload_and_scan(file_path: str) -> dict:
    """
    Upload an authorized APK, AAB, or Android source ZIP and run static analysis.
    The file must be inside MOBSF_UPLOAD_ROOT. Returns the MobSF scan hash.
    """
    path = _validate_upload(file_path)
    uploaded = _api("upload", file_path=path, timeout=HTTP_TIMEOUT * 3)

    if not isinstance(uploaded, dict) or not uploaded.get("hash"):
        raise RuntimeError(f"MobSF upload did not return a scan hash: {uploaded}")

    scan_hash = _validate_hash(str(uploaded["hash"]))
    scan_result = _api(
        "scan",
        {"hash": scan_hash, "re_scan": "0"},
        timeout=SCAN_TIMEOUT,
    )
    log.info("Static scan completed for %s (hash %s)", path.name, scan_hash)

    return {
        "filename": path.name,
        "hash": scan_hash,
        "scan_result": scan_result,
    }


@mcp.tool()
def mobsf_android_summary(scan_hash: str) -> dict:
    """
    Return a triage summary: app identity, SDK levels, manifest/code/certificate
    findings grouped by severity, dangerous permissions, secrets, and trackers.
    """
    validated_hash = _validate_hash(scan_hash)
    report = _api("report_json", {"hash": validated_hash})
    if not isinstance(report, dict):
        raise RuntimeError("Unexpected report format from MobSF.")
    return _summarize(report)


@mcp.tool()
def mobsf_get_json_report(scan_hash: str) -> dict:
    """Retrieve the full raw MobSF JSON report for a scan hash."""
    report = _api("report_json", {"hash": _validate_hash(scan_hash)})
    if not isinstance(report, dict):
        raise RuntimeError("Unexpected report format from MobSF.")
    return report


@mcp.tool()
def mobsf_search(query: str) -> dict:
    """Search existing MobSF scans by filename, package name, or hash."""
    if not isinstance(query, str) or not query.strip() or len(query) > 256:
        raise ValueError("query must contain 1-256 characters.")
    result = _api("search", {"query": query.strip()})
    if not isinstance(result, dict):
        raise RuntimeError("Unexpected search response from MobSF.")
    return result


@mcp.tool()
def mobsf_recent_scans(page: int = 1, page_size: int = 20) -> dict:
    """List recent MobSF scans; page_size is limited to 100."""
    page = max(1, int(page))
    page_size = max(1, min(int(page_size), 100))
    result = _api(
        "scans",
        {"page": str(page), "page_size": str(page_size)},
    )
    if not isinstance(result, dict):
        raise RuntimeError("Unexpected scans response from MobSF.")
    return result


@mcp.tool()
def mobsf_scan_logs(scan_hash: str) -> dict:
    """Retrieve MobSF scan logs for a validated scan hash."""
    result = _api("scan_logs", {"hash": _validate_hash(scan_hash)})
    if not isinstance(result, dict):
        raise RuntimeError("Unexpected scan logs response from MobSF.")
    return result


@mcp.tool()
def mobsf_download_pdf_report(scan_hash: str) -> dict:
    """Download a MobSF PDF report into MOBSF_REPORT_DIR."""
    validated_hash = _validate_hash(scan_hash)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    pdf = _api(
        "download_pdf",
        {"hash": validated_hash},
        timeout=SCAN_TIMEOUT,
    )
    if not isinstance(pdf, bytes) or not pdf.startswith(b"%PDF"):
        raise RuntimeError("MobSF did not return a valid PDF report.")

    output_path = REPORT_DIR / f"{validated_hash}.pdf"
    output_path.write_bytes(pdf)

    return {
        "saved": True,
        "path": str(output_path),
        "size_bytes": len(pdf),
    }


if __name__ == "__main__":
    # FastMCP uses stdio by default, as expected by Claude Desktop.
    mcp.run()
