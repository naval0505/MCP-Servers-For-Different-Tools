import logging
import re
import subprocess
from pathlib import Path

from mcp.server.mcpserver import MCPServer


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
PCAP_DIR = (BASE_DIR / "pcaps").resolve()

TSHARK = Path(r"C:\Program Files\Wireshark\tshark.exe")
CAPINFOS = Path(r"C:\Program Files\Wireshark\capinfos.exe")

MAX_OUTPUT = 200_000
MAX_PACKETS = 5_000
COMMAND_TIMEOUT = 120


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger("wireshark-mcp")


# ============================================================
# MCP SERVER
# ============================================================

mcp = MCPServer("Wireshark MCP")


# ============================================================
# ENVIRONMENT
# ============================================================

def validate_environment():
    if not TSHARK.is_file():
        raise RuntimeError(
            f"TShark not found: {TSHARK}"
        )

    if not CAPINFOS.is_file():
        raise RuntimeError(
            f"capinfos not found: {CAPINFOS}"
        )

    PCAP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================
# PCAP SECURITY
# ============================================================

def resolve_pcap(filename: str) -> Path:
    if not filename:
        raise ValueError(
            "PCAP filename cannot be empty."
        )

    requested = Path(filename)

    if requested.is_absolute():
        raise ValueError(
            "Absolute paths are not allowed."
        )

    pcap = (PCAP_DIR / requested).resolve()

    try:
        pcap.relative_to(PCAP_DIR)
    except ValueError:
        raise ValueError(
            "Path traversal is not allowed."
        )

    if pcap.suffix.lower() not in {
        ".pcap",
        ".pcapng",
        ".cap",
    }:
        raise ValueError(
            "Only .pcap, .pcapng and .cap files are supported."
        )

    if not pcap.is_file():
        raise FileNotFoundError(
            f"PCAP not found: {filename}"
        )

    return pcap


# ============================================================
# TSHARK EXECUTION
# ============================================================

def run_tshark(
    args: list[str],
    timeout: int = COMMAND_TIMEOUT,
) -> str:

    validate_environment()

    command = [
        str(TSHARK),
        *args,
    ]

    logger.info(
        "Running TShark: %s",
        command,
    )

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=False,
    )

    if result.returncode != 0:
        error = (
            result.stderr.strip()
            or "TShark returned an error."
        )

        raise RuntimeError(error)

    output = result.stdout

    if len(output) > MAX_OUTPUT:
        output = (
            output[:MAX_OUTPUT]
            + "\n...[OUTPUT TRUNCATED]"
        )

    return output


# ============================================================
# CAPINFOS
# ============================================================

def run_capinfos(pcap: Path) -> str:

    validate_environment()

    result = subprocess.run(
        [
            str(CAPINFOS),
            str(pcap),
        ],
        capture_output=True,
        text=True,
        timeout=COMMAND_TIMEOUT,
        shell=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip()
            or "capinfos returned an error."
        )

    return result.stdout


# ============================================================
# VALIDATION
# ============================================================

def validate_filter(
    display_filter: str,
) -> str:

    if not display_filter:
        raise ValueError(
            "Display filter cannot be empty."
        )

    if len(display_filter) > 1000:
        raise ValueError(
            "Display filter is too long."
        )

    return display_filter


def validate_field(
    field: str,
) -> str:

    if not re.fullmatch(
        r"[A-Za-z0-9_.-]+",
        field,
    ):
        raise ValueError(
            f"Invalid field name: {field}"
        )

    return field


# ============================================================
# TOOL 1
# LIST PCAPS
# ============================================================

@mcp.tool()
def list_pcaps() -> str:
    """
    List all PCAP files available
    inside the MCP pcaps directory.
    """

    validate_environment()

    files = sorted(
        p.name
        for p in PCAP_DIR.iterdir()
        if p.is_file()
        and p.suffix.lower()
        in {
            ".pcap",
            ".pcapng",
            ".cap",
        }
    )

    if not files:
        return (
            "No PCAP files found in the pcaps directory."
        )

    return "\n".join(files)


# ============================================================
# TOOL 2
# PCAP INFO
# ============================================================

@mcp.tool()
def pcap_info(
    filename: str,
) -> str:
    """
    Show detailed metadata about a PCAP
    using Wireshark capinfos.
    """

    pcap = resolve_pcap(filename)

    return run_capinfos(pcap)


# ============================================================
# TOOL 3
# CAPTURE OVERVIEW
# ============================================================

@mcp.tool()
def capture_overview(
    filename: str,
) -> str:
    """
    Show a protocol hierarchy overview
    of a PCAP.
    """

    pcap = resolve_pcap(filename)

    return run_tshark([
        "-r",
        str(pcap),
        "-q",
        "-z",
        "io,phs",
    ])


# ============================================================
# TOOL 4
# PACKET SUMMARY
# ============================================================

@mcp.tool()
def packet_summary(
    filename: str,
    packet_count: int = 100,
) -> str:
    """
    Show packet number, time, protocol,
    source, destination and information.
    """

    pcap = resolve_pcap(filename)

    packet_count = max(
        1,
        min(
            packet_count,
            MAX_PACKETS,
        ),
    )

    return run_tshark([
        "-r",
        str(pcap),
        "-c",
        str(packet_count),
        "-T",
        "fields",
        "-E",
        "separator=|",
        "-e",
        "frame.number",
        "-e",
        "frame.time",
        "-e",
        "frame.len",
        "-e",
        "_ws.col.Protocol",
        "-e",
        "_ws.col.Source",
        "-e",
        "_ws.col.Destination",
        "-e",
        "_ws.col.Info",
    ])


# ============================================================
# TOOL 5
# DISPLAY FILTER
# ============================================================

@mcp.tool()
def display_filter(
    filename: str,
    filter_expression: str,
    packet_count: int = 200,
) -> str:
    """
    Apply a Wireshark display filter.
    """

    pcap = resolve_pcap(filename)

    filter_expression = validate_filter(
        filter_expression
    )

    packet_count = max(
        1,
        min(
            packet_count,
            MAX_PACKETS,
        ),
    )

    return run_tshark([
        "-r",
        str(pcap),
        "-Y",
        filter_expression,
        "-c",
        str(packet_count),
        "-T",
        "fields",
        "-E",
        "separator=|",
        "-e",
        "frame.number",
        "-e",
        "frame.time",
        "-e",
        "_ws.col.Protocol",
        "-e",
        "_ws.col.Source",
        "-e",
        "_ws.col.Destination",
        "-e",
        "_ws.col.Info",
    ])


# ============================================================
# TOOL 6
# EXTRACT FIELDS
# ============================================================

@mcp.tool()
def extract_fields(
    filename: str,
    field: str,
    packet_count: int = 500,
) -> str:
    """
    Extract a Wireshark field from packets.

    Example fields:
    ip.src
    ip.dst
    tcp.port
    dns.qry.name
    http.host
    http.request.uri
    """

    pcap = resolve_pcap(filename)

    field = validate_field(field)

    packet_count = max(
        1,
        min(
            packet_count,
            MAX_PACKETS,
        ),
    )

    return run_tshark([
        "-r",
        str(pcap),
        "-c",
        str(packet_count),
        "-T",
        "fields",
        "-E",
        "header=y",
        "-E",
        "separator=|",
        "-e",
        field,
    ])


# ============================================================
# TOOL 7
# PROTOCOL HIERARCHY
# ============================================================

@mcp.tool()
def protocol_hierarchy(
    filename: str,
) -> str:
    """
    Show protocol hierarchy statistics.
    """

    pcap = resolve_pcap(filename)

    return run_tshark([
        "-r",
        str(pcap),
        "-q",
        "-z",
        "io,phs",
    ])


# ============================================================
# TOOL 8
# CONVERSATIONS
# ============================================================

@mcp.tool()
def conversations(
    filename: str,
    protocol: str = "ip",
) -> str:
    """
    Show network conversations.

    Supported:
    eth
    ip
    ipv6
    tcp
    udp
    """

    pcap = resolve_pcap(filename)

    protocol = protocol.lower()

    allowed = {
        "eth",
        "ip",
        "ipv6",
        "tcp",
        "udp",
    }

    if protocol not in allowed:
        raise ValueError(
            "Unsupported protocol."
        )

    return run_tshark([
        "-r",
        str(pcap),
        "-q",
        "-z",
        f"conv,{protocol}",
    ])


# ============================================================
# TOOL 9
# ENDPOINTS
# ============================================================

@mcp.tool()
def endpoints(
    filename: str,
    protocol: str = "ip",
) -> str:
    """
    Show network endpoints.
    """

    pcap = resolve_pcap(filename)

    protocol = protocol.lower()

    allowed = {
        "eth",
        "ip",
        "ipv6",
        "tcp",
        "udp",
    }

    if protocol not in allowed:
        raise ValueError(
            "Unsupported protocol."
        )

    return run_tshark([
        "-r",
        str(pcap),
        "-q",
        "-z",
        f"endpoints,{protocol}",
    ])


# ============================================================
# TOOL 10
# DNS QUERIES
# ============================================================

@mcp.tool()
def dns_queries(
    filename: str,
) -> str:
    """
    Extract DNS queries and responses.
    """

    pcap = resolve_pcap(filename)

    return run_tshark([
        "-r",
        str(pcap),
        "-Y",
        "dns",
        "-T",
        "fields",
        "-E",
        "separator=|",
        "-e",
        "frame.number",
        "-e",
        "ip.src",
        "-e",
        "ip.dst",
        "-e",
        "dns.qry.name",
        "-e",
        "dns.qry.type",
        "-e",
        "dns.a",
        "-e",
        "dns.aaaa",
    ])


# ============================================================
# TOOL 11
# HTTP REQUESTS
# ============================================================

@mcp.tool()
def http_requests(
    filename: str,
) -> str:
    """
    Extract HTTP requests.
    """

    pcap = resolve_pcap(filename)

    return run_tshark([
        "-r",
        str(pcap),
        "-Y",
        "http.request",
        "-T",
        "fields",
        "-E",
        "separator=|",
        "-e",
        "frame.number",
        "-e",
        "ip.src",
        "-e",
        "ip.dst",
        "-e",
        "http.request.method",
        "-e",
        "http.host",
        "-e",
        "http.request.uri",
        "-e",
        "http.user_agent",
    ])


# ============================================================
# TOOL 12
# TLS ANALYSIS
# ============================================================

@mcp.tool()
def tls_analysis(
    filename: str,
) -> str:
    """
    Extract TLS-related information.
    """

    pcap = resolve_pcap(filename)

    return run_tshark([
        "-r",
        str(pcap),
        "-Y",
        "tls",
        "-T",
        "fields",
        "-E",
        "separator=|",
        "-e",
        "frame.number",
        "-e",
        "ip.src",
        "-e",
        "ip.dst",
        "-e",
        "tcp.srcport",
        "-e",
        "tcp.dstport",
        "-e",
        "tls.record.version",
        "-e",
        "tls.handshake.type",
        "-e",
        "tls.handshake.extensions_server_name",
    ])


# ============================================================
# TOOL 13
# ARP ACTIVITY
# ============================================================

@mcp.tool()
def arp_activity(
    filename: str,
) -> str:
    """
    Extract ARP activity.
    """

    pcap = resolve_pcap(filename)

    return run_tshark([
        "-r",
        str(pcap),
        "-Y",
        "arp",
        "-T",
        "fields",
        "-E",
        "separator=|",
        "-e",
        "frame.number",
        "-e",
        "arp.opcode",
        "-e",
        "arp.src.proto_ipv4",
        "-e",
        "arp.src.hw_mac",
        "-e",
        "arp.dst.proto_ipv4",
        "-e",
        "arp.dst.hw_mac",
    ])


# ============================================================
# TOOL 14
# TCP ANALYSIS
# ============================================================

@mcp.tool()
def tcp_analysis(
    filename: str,
) -> str:
    """
    Analyze TCP flags and endpoints.
    """

    pcap = resolve_pcap(filename)

    return run_tshark([
        "-r",
        str(pcap),
        "-Y",
        "tcp",
        "-T",
        "fields",
        "-E",
        "separator=|",
        "-e",
        "frame.number",
        "-e",
        "ip.src",
        "-e",
        "tcp.srcport",
        "-e",
        "ip.dst",
        "-e",
        "tcp.dstport",
        "-e",
        "tcp.flags",
        "-e",
        "tcp.flags.syn",
        "-e",
        "tcp.flags.ack",
        "-e",
        "tcp.flags.fin",
        "-e",
        "tcp.flags.reset",
    ])


# ============================================================
# TOOL 15
# TOP TALKERS
# ============================================================

@mcp.tool()
def top_talkers(
    filename: str,
) -> str:
    """
    Show IP conversation statistics.
    """

    pcap = resolve_pcap(filename)

    return run_tshark([
        "-r",
        str(pcap),
        "-q",
        "-z",
        "conv,ip",
    ])


# ============================================================
# TOOL 16
# CLEARTEXT PROTOCOLS
# ============================================================

@mcp.tool()
def cleartext_protocols(
    filename: str,
) -> str:
    """
    Find common cleartext protocols such as
    HTTP, FTP, Telnet, SMTP, POP and IMAP.
    """

    pcap = resolve_pcap(filename)

    return run_tshark([
        "-r",
        str(pcap),
        "-Y",
        "http || ftp || telnet || smtp || pop || imap",
        "-T",
        "fields",
        "-E",
        "separator=|",
        "-e",
        "frame.number",
        "-e",
        "_ws.col.Protocol",
        "-e",
        "ip.src",
        "-e",
        "ip.dst",
        "-e",
        "_ws.col.Info",
    ])


# ============================================================
# TOOL 17
# SUSPICIOUS INDICATORS
# ============================================================

@mcp.tool()
def suspicious_indicators(
    filename: str,
) -> str:
    """
    Identify network traffic that deserves
    further investigation.

    This does not automatically classify traffic
    as malicious.
    """

    pcap = resolve_pcap(filename)

    suspicious_filter = (
        "tcp.flags.reset == 1"
        " || tcp.analysis.retransmission"
        " || tcp.analysis.lost_segment"
        " || dns.qry.name"
        " || http.request"
        " || ftp"
        " || telnet"
        " || arp"
    )

    return run_tshark([
        "-r",
        str(pcap),
        "-Y",
        suspicious_filter,
        "-c",
        str(MAX_PACKETS),
        "-T",
        "fields",
        "-E",
        "separator=|",
        "-e",
        "frame.number",
        "-e",
        "frame.time",
        "-e",
        "_ws.col.Protocol",
        "-e",
        "_ws.col.Source",
        "-e",
        "_ws.col.Destination",
        "-e",
        "_ws.col.Info",
    ])


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    validate_environment()

    logger.info(
        "Wireshark MCP server starting..."
    )

    logger.info(
        "PCAP directory: %s",
        PCAP_DIR,
    )

    logger.info(
        "TShark: %s",
        TSHARK,
    )

    logger.info(
        "capinfos: %s",
        CAPINFOS,
    )

    mcp.run(transport="stdio")
