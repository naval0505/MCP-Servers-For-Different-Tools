#!/usr/bin/env python3

import subprocess
import shutil
from typing import Optional

from fastmcp import FastMCP

mcp = FastMCP("nmap-mcp")


def check_nmap() -> str:
    """Check whether Nmap is installed."""
    nmap_path = shutil.which("nmap")

    if not nmap_path:
        return "ERROR: Nmap is not installed or not found in PATH."

    try:
        result = subprocess.run(
            [nmap_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )

        return result.stdout.strip()

    except Exception as e:
        return f"ERROR: {e}"


def run_nmap(
    arguments: list[str],
    timeout: int = 120
) -> str:
    """Execute an Nmap command and return its output."""

    nmap_path = shutil.which("nmap")

    if not nmap_path:
        return "ERROR: Nmap is not installed or not found in PATH."

    command = [nmap_path] + arguments

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        output = []

        if result.stdout:
            output.append(result.stdout.strip())

        if result.stderr:
            output.append(
                "\n--- STDERR ---\n"
                + result.stderr.strip()
            )

        output.append(
            f"\n--- EXIT CODE: {result.returncode} ---"
        )

        return "\n".join(output)

    except subprocess.TimeoutExpired:
        return f"ERROR: Nmap scan timed out after {timeout} seconds."

    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool()
def nmap_version() -> str:
    """
    Show the installed Nmap version.
    """
    return check_nmap()


@mcp.tool()
def host_discovery(
    target: str,
    timeout: int = 120
) -> str:
    """
    Discover live hosts without performing a normal port scan.

    Example target:
    192.168.1.0/24
    """

    return run_nmap(
        ["-sn", target],
        timeout
    )


@mcp.tool()
def port_scan(
    target: str,
    ports: Optional[str] = None,
    timeout: int = 120
) -> str:
    """
    Perform a TCP port scan.

    ports examples:
    22
    22,80,443
    1-1000

    If ports is omitted, Nmap's default port selection is used.
    """

    arguments = []

    if ports:
        arguments.extend(["-p", ports])

    arguments.append(target)

    return run_nmap(
        arguments,
        timeout
    )


@mcp.tool()
def service_detection(
    target: str,
    ports: Optional[str] = None,
    timeout: int = 180
) -> str:
    """
    Detect services and versions running on discovered ports.
    """

    arguments = ["-sV"]

    if ports:
        arguments.extend(["-p", ports])

    arguments.append(target)

    return run_nmap(
        arguments,
        timeout
    )


@mcp.tool()
def os_detection(
    target: str,
    timeout: int = 180
) -> str:
    """
    Attempt operating-system detection.
    """

    return run_nmap(
        ["-O", target],
        timeout
    )


@mcp.tool()
def comprehensive_scan(
    target: str,
    timeout: int = 300
) -> str:
    """
    Perform a comprehensive Nmap scan using:
    - Service/version detection
    - OS detection
    - Default NSE scripts
    - Traceroute
    """

    return run_nmap(
        ["-A", target],
        timeout
    )


@mcp.tool()
def nse_scan(
    target: str,
    script: str = "default",
    ports: Optional[str] = None,
    timeout: int = 180
) -> str:
    """
    Run an Nmap NSE script or script category.

    Examples:
    default
    vuln
    http-title
    ssl-enum-ciphers

    Use only against systems you are authorized to test.
    """

    arguments = [
        "-sV",
        "--script",
        script
    ]

    if ports:
        arguments.extend(["-p", ports])

    arguments.append(target)

    return run_nmap(
        arguments,
        timeout
    )


@mcp.tool()
def udp_scan(
    target: str,
    ports: Optional[str] = None,
    timeout: int = 300
) -> str:
    """
    Perform a UDP port scan.

    UDP scanning can take significantly longer than TCP scanning.
    """

    arguments = ["-sU"]

    if ports:
        arguments.extend(["-p", ports])

    arguments.append(target)

    return run_nmap(
        arguments,
        timeout
    )


@mcp.tool()
def top_ports_scan(
    target: str,
    number: int = 100,
    timeout: int = 180
) -> str:
    """
    Scan the most common N ports.

    Example:
    number=100
    number=1000
    """

    if number < 1 or number > 10000:
        return "ERROR: number must be between 1 and 10000."

    return run_nmap(
        ["--top-ports", str(number), target],
        timeout
    )


@mcp.tool()
def aggressive_top_ports(
    target: str,
    number: int = 100,
    timeout: int = 300
) -> str:
    """
    Perform service/version detection, OS detection and default
    NSE scripts against the most common ports.
    """

    if number < 1 or number > 10000:
        return "ERROR: number must be between 1 and 10000."

    return run_nmap(
        [
            "-A",
            "--top-ports",
            str(number),
            target
        ],
        timeout
    )


@mcp.tool()
def ping_scan(
    target: str,
    timeout: int = 120
) -> str:
    """
    Perform a basic ICMP/host availability scan.
    """

    return run_nmap(
        ["-PE", "-sn", target],
        timeout
    )


@mcp.tool()
def traceroute(
    target: str,
    timeout: int = 180
) -> str:
    """
    Perform Nmap traceroute.
    """

    return run_nmap(
        ["--traceroute", "-sn", target],
        timeout
    )


@mcp.tool()
def save_scan(
    target: str,
    output_file: str,
    scan_type: str = "basic",
    timeout: int = 180
) -> str:
    """
    Run a scan and save the results to an Nmap output file.

    scan_type options:
    basic
    service
    aggressive
    top100
    vuln

    The output file is passed to Nmap with -oN.
    """

    scan_map = {
        "basic": [],
        "service": ["-sV"],
        "aggressive": ["-A"],
        "top100": ["--top-ports", "100"],
        "vuln": ["--script", "vuln"],
    }

    if scan_type not in scan_map:
        return (
            "ERROR: Invalid scan_type. "
            "Use: basic, service, aggressive, top100, vuln."
        )

    arguments = scan_map[scan_type].copy()

    arguments.extend([
        "-oN",
        output_file,
        target
    ])

    return run_nmap(
        arguments,
        timeout
    )


@mcp.tool()
def custom_nmap(
    arguments: str,
    timeout: int = 300
) -> str:
    """
    Run a custom Nmap argument string.

    Example:
    -sV -p 22,80,443 192.168.1.10

    Use only against systems you are authorized to scan.
    """

    try:
        import shlex

        parsed_arguments = shlex.split(arguments)

        if not parsed_arguments:
            return "ERROR: No Nmap arguments supplied."

        return run_nmap(
            parsed_arguments,
            timeout
        )

    except Exception as e:
        return f"ERROR: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
