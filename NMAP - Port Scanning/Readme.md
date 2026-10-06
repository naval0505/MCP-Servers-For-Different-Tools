# Nmap MCP Server

An MCP (Model Context Protocol) server that connects **Nmap** with **Claude Desktop**, allowing Claude to perform authorized network reconnaissance and security enumeration through Nmap.

The server exposes common Nmap capabilities as MCP tools, making it possible to perform host discovery, port scanning, service detection, OS detection, NSE scanning, traceroute, and other network-analysis tasks directly through an AI assistant.

## Features

- Nmap version detection
- Host discovery
- TCP port scanning
- Service and version detection
- Operating system detection
- Comprehensive Nmap scanning
- NSE script scanning
- UDP scanning
- Top-port scanning
- Aggressive top-port scanning
- Ping scanning
- Nmap traceroute
- Save scan results to files
- Custom Nmap command execution

## Architecture

```text
┌─────────────────────┐
│    Claude Desktop   │
└──────────┬──────────┘
           │
           │ MCP / stdio
           ▼
┌─────────────────────┐
│    Nmap MCP Server  │
│       Python        │
└──────────┬──────────┘
           │
           │ Nmap commands
           ▼
┌─────────────────────┐
│        Nmap         │
│ Network Scanner     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Authorized Target   │
│ Host / Network      │
└─────────────────────┘
```

## Requirements

- Linux
- Python 3
- Nmap
- Claude Desktop
- FastMCP
- MCP Python SDK

This project uses the system Python installation and does **not require a virtual environment**.

## Installation

### 1. Install Nmap

On Kali Linux:

```bash
sudo apt update
sudo apt install nmap
```

Verify the installation:

```bash
nmap --version
```

You can also verify the executable location:

```bash
which nmap
```

Typical output:

```text
/usr/bin/nmap
```

### 2. Install Python Dependencies

Install FastMCP and the MCP SDK:

```bash
/usr/bin/python -m pip install --break-system-packages fastmcp mcp
```

If Kali reports a dependency conflict with an existing system package, use:

```bash
/usr/bin/python -m pip install --break-system-packages --ignore-installed typing-extensions
```

Then:

```bash
/usr/bin/python -m pip install --break-system-packages --ignore-installed fastmcp mcp
```

Verify the installation:

```bash
/usr/bin/python -c "import fastmcp; import mcp; print('IMPORTS OK')"
```

## Setup

Create a directory for the MCP server:

```bash
mkdir -p /home/kali/mcp/nmap
```

Create the server file:

```bash
nano /home/kali/mcp/nmap/nmap_server.py
```

Paste the `nmap_server.py` code into the file and save it.

Verify the file:

```bash
ls -l /home/kali/mcp/nmap/nmap_server.py
```

## Test the MCP Server

Run the server directly:

```bash
/usr/bin/python /home/kali/mcp/nmap/nmap_server.py
```

If there are no Python/import errors, the server is ready to be connected to Claude Desktop.

## Claude Desktop Configuration

Add the following MCP server configuration:

```json
{
  "mcpServers": {
    "nmap-mcp": {
      "command": "/usr/bin/python",
      "args": [
        "/home/kali/mcp/nmap/nmap_server.py"
      ]
    }
  }
}
```

Make sure the path matches the actual location of `nmap_server.py`.

After updating the configuration, restart Claude Desktop.

## Available MCP Tools

| Tool | Purpose |
|---|---|
| `nmap_version` | Display the installed Nmap version |
| `host_discovery` | Discover live hosts |
| `port_scan` | Perform TCP port scanning |
| `service_detection` | Detect services and versions |
| `os_detection` | Attempt OS detection |
| `comprehensive_scan` | Run an aggressive Nmap scan |
| `nse_scan` | Run Nmap NSE scripts |
| `udp_scan` | Scan UDP ports |
| `top_ports_scan` | Scan the most common ports |
| `aggressive_top_ports` | Combine aggressive scanning with top ports |
| `ping_scan` | Perform host availability discovery |
| `traceroute` | Perform Nmap traceroute |
| `save_scan` | Save scan output to a file |
| `custom_nmap` | Run custom Nmap arguments |

## Example Prompts

Once connected to Claude, you can ask:

```text
Check whether Nmap is installed.
```

```text
Discover live hosts on 192.168.1.0/24.
```

```text
Scan ports 22,80,443 on 192.168.1.10.
```

```text
Detect the services and versions running on 192.168.1.10.
```

```text
Perform OS detection on 192.168.1.10.
```

```text
Scan the top 100 ports on 192.168.1.10.
```

```text
Run an Nmap service detection scan against this host.
```

```text
Run the default NSE scripts against the authorized target.
```

```text
Perform a comprehensive Nmap scan and summarize the results.
```

```text
Run a traceroute to the target.
```

## Example Workflow

A typical reconnaissance workflow can look like:

```text
Claude
  │
  ▼
Host Discovery
  │
  ▼
Port Scan
  │
  ▼
Service Detection
  │
  ▼
OS Detection
  │
  ▼
NSE Enumeration
  │
  ▼
Security Analysis
```

For example:

```text
1. Discover live hosts
2. Identify open ports
3. Determine running services
4. Identify service versions
5. Perform OS detection
6. Run appropriate NSE scripts
7. Analyze and summarize the results
```

## Custom Nmap Scans

The `custom_nmap` tool allows you to provide Nmap arguments directly.

Example:

```text
-sV -p 22,80,443 192.168.1.10
```

This makes the MCP server flexible enough to support Nmap options that are not exposed through the dedicated tools.

## Security Considerations

This project is intended for:

- Authorized penetration testing
- Security research
- Network administration
- CTF environments
- Cybersecurity education
- Lab environments
- Infrastructure assessment

**Only scan systems and networks that you own or have explicit authorization to test.**

Nmap is an active network-scanning tool. Scanning systems without authorization may violate organizational policies, terms of service, or applicable laws.

The MCP server does not provide a security boundary around Nmap. Users should operate it in an environment appropriate for the targets being assessed.

## Why MCP?

Normally, an analyst needs to manually execute Nmap commands from a terminal.

With MCP, Claude can act as an interface to Nmap:

```text
┌───────────────┐
│ Claude        │
└───────┬───────┘
        │
        │ MCP
        ▼
┌───────────────┐
│ Nmap MCP      │
│ Server        │
└───────┬───────┘
        │
        │ Commands
        ▼
┌───────────────┐
│ Nmap          │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ Network       │
│ Target        │
└───────────────┘
```

This allows the AI assistant to help organize reconnaissance workflows, interpret scan results, and provide a natural-language interface to Nmap.

## Project Goals

The project aims to provide a simple bridge between:

**AI assistants + MCP + Nmap + cybersecurity workflows**

Future improvements could include:

- XML output parsing
- Structured scan results
- Better vulnerability-result parsing
- Automatic service enumeration
- Scan-result summaries
- Host/service inventories
- Improved NSE integration
- Output filtering
- Scan profiles
- JSON-based results
- Integration with additional security tools

## Troubleshooting

### Nmap not found

Check:

```bash
which nmap
```

If nothing is returned:

```bash
sudo apt install nmap
```

### Python cannot import FastMCP

Test:

```bash
/usr/bin/python -c "import fastmcp; print('FastMCP OK')"
```

If it fails:

```bash
/usr/bin/python -m pip install --break-system-packages fastmcp
```

### Claude says the MCP server disconnected

First verify the server path:

```bash
ls -l /home/kali/mcp/nmap/nmap_server.py
```

Then run it manually:

```bash
/usr/bin/python /home/kali/mcp/nmap/nmap_server.py
```

Make sure the exact same path is used in the Claude Desktop configuration.

## Disclaimer

This project is provided for authorized security testing, research, education, and defensive purposes.

Do not use this tool to scan networks or systems without appropriate authorization.

The author is not responsible for misuse of this software.

## License

Add your preferred license here.

Example:

```text
MIT License
```

## Author

Built as part of an MCP-based cybersecurity tooling project focused on connecting AI assistants with practical security and reconnaissance tools.
