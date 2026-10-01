# Wireshark MCP Server

A Windows-based Model Context Protocol (MCP) server that connects Claude Desktop with Wireshark's **TShark** and **capinfos** command-line tools.

The server allows Claude to analyze PCAP files through structured MCP tools instead of manually running Wireshark/TShark commands.

---

## Features

The server currently provides 17 MCP tools:

1. `list_pcaps` — List available PCAP files
2. `pcap_info` — Display PCAP metadata using `capinfos`
3. `capture_overview` — Show protocol hierarchy
4. `packet_summary` — Display packet summaries
5. `display_filter` — Apply Wireshark display filters
6. `extract_fields` — Extract specific Wireshark fields
7. `protocol_hierarchy` — Show protocol hierarchy statistics
8. `conversations` — Display network conversations
9. `endpoints` — Display network endpoints
10. `dns_queries` — Extract DNS queries and responses
11. `http_requests` — Extract HTTP requests
12. `tls_analysis` — Extract TLS information
13. `arp_activity` — Extract ARP traffic
14. `tcp_analysis` — Analyze TCP flags and endpoints
15. `top_talkers` — Display IP conversation statistics
16. `cleartext_protocols` — Find common cleartext protocols
17. `suspicious_indicators` — Identify traffic that deserves further investigation

> `suspicious_indicators` provides indicators for investigation. It does not automatically classify traffic as malicious.

---

# Architecture

```text
                    Claude Desktop
                          │
                          │ MCP / stdio
                          ▼
                ┌─────────────────────┐
                │   Wireshark MCP     │
                │      server.py      │
                └──────────┬──────────┘
                           │
                ┌──────────┴──────────┐
                │                     │
                ▼                     ▼
             TShark                capinfos
                │                     │
                └──────────┬──────────┘
                           ▼
                         PCAP
```

Claude communicates with the MCP server over stdio.

The MCP server then executes fixed TShark/capinfos commands against PCAP files stored in the project's `pcaps` directory.

---

# Requirements

## Operating System

Tested on:

```text
Windows 11 25H2
```

## Software

Required:

* Python 3.13.x
* Wireshark
* TShark
* capinfos
* Claude Desktop
* MCP Python SDK

The tested environment used:

```text
Python       3.13.3
pip          26.2.1
MCP          2.2.0
Wireshark    4.6.9
Npcap        1.88
```

---

# Wireshark Installation

Install Wireshark normally.

The project expects the following executables:

```text
C:\Program Files\Wireshark\tshark.exe
C:\Program Files\Wireshark\capinfos.exe
```

Verify TShark:

```powershell
& "C:\Program Files\Wireshark\tshark.exe" --version
```

Verify capinfos:

```powershell
& "C:\Program Files\Wireshark\capinfos.exe" --version
```

---

# Project Setup

Create the project directory:

```powershell
mkdir "C:\Users\Dharmesh\Desktop\MCP_SERVER"
cd "C:\Users\Dharmesh\Desktop\MCP_SERVER"
```

Create the PCAP directory:

```powershell
mkdir pcaps
```

---

# Python Virtual Environment

Create the virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

You should see:

```text
(.venv) PS C:\Users\Dharmesh\Desktop\MCP_SERVER>
```

Verify Python:

```powershell
python --version
```

Verify pip:

```powershell
python -m pip --version
```

---

# Install MCP

Install the Python MCP SDK:

```powershell
python -m pip install mcp
```

Verify:

```powershell
python -m pip show mcp
```

The tested environment uses:

```text
mcp 2.2.0
```

---

# Important Python Environment Note

When the virtual environment is activated, use:

```powershell
python
```

instead of:

```powershell
python3.13.exe
```

or another system Python executable.

The MCP package was installed inside the virtual environment.

Using the system Python can result in:

```text
ModuleNotFoundError: No module named 'mcp'
```

---

# PCAP Directory

PCAP files must be placed inside:

```text
C:\Users\Dharmesh\Desktop\MCP_SERVER\pcaps
```

Example:

```text
MCP_SERVER
│
├── .venv
├── pcaps
│   └── example.pcap
└── server.py
```

The server does not allow arbitrary PCAP paths.

---

# Example PCAP

The current test capture used during development is:

```text
2014-11-08-traffic-analysis-exercise.pcap
```

Expected location:

```text
C:\Users\Dharmesh\Desktop\MCP_SERVER\pcaps\2014-11-08-traffic-analysis-exercise.pcap
```

---

# Testing TShark

Before testing MCP, verify that TShark can directly read the PCAP.

Run:

```powershell
& "C:\Program Files\Wireshark\tshark.exe" -r ".\pcaps\2014-11-08-traffic-analysis-exercise.pcap" -c 5
```

A successful result should display packet information similar to:

```text
1  03:00:05.040188  172.16.165.159  38648  172.16.165.2  53  DNS
2  03:00:05.271769  172.16.165.2    53     172.16.165.159 38648 DNS
3  03:00:05.632550  172.16.165.159  36761  72.47.224.159 80 TCP
```

This confirms that:

* Wireshark is installed
* TShark works
* The PCAP exists
* TShark can parse the capture

---

# Testing the MCP Server

Compile the server first:

```powershell
python -m py_compile .\server.py
```

If there is no output, compilation succeeded.

Start the MCP server:

```powershell
python .\server.py
```

Expected startup output:

```text
Wireshark MCP server starting...
PCAP directory: C:\Users\Dharmesh\Desktop\MCP_SERVER\pcaps
TShark: C:\Program Files\Wireshark\tshark.exe
capinfos: C:\Program Files\Wireshark\capinfos.exe
```

The server will remain running because it is waiting for an MCP client.

Press:

```text
Ctrl+C
```

to stop it during manual testing.

---

# Claude Desktop Configuration

Claude Desktop can launch the MCP server automatically.

The Windows Claude configuration directory is normally:

```text
%APPDATA%\Claude
```

The configuration file is:

```text
claude_desktop_config.json
```

Open the directory with:

```text
Win + R
```

then:

```text
%APPDATA%\Claude
```

---

# MCP Configuration

Add the following server configuration:

```json
{
  "mcpServers": {
    "wireshark": {
      "command": "C:\\Users\\Dharmesh\\Desktop\\MCP_SERVER\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\Dharmesh\\Desktop\\MCP_SERVER\\server.py"
      ]
    }
  }
}
```

If `claude_desktop_config.json` already contains other MCP servers, add the `wireshark` entry without deleting the existing configurations.

---

# Why the Virtual Environment Python Is Used

The configuration intentionally uses:

```text
C:\Users\Dharmesh\Desktop\MCP_SERVER\.venv\Scripts\python.exe
```

instead of:

```text
python
```

because this guarantees that Claude starts the server using the Python environment containing the MCP SDK.

The server script is:

```text
C:\Users\Dharmesh\Desktop\MCP_SERVER\server.py
```

---

# Restart Claude Desktop

After modifying:

```text
claude_desktop_config.json
```

completely exit Claude Desktop and start it again.

Claude should then launch:

```text
.venv\Scripts\python.exe
```

which runs:

```text
server.py
```

---

# Testing From Claude

Once the MCP server is connected, ask Claude:

```text
Use the Wireshark MCP server.

First call list_pcaps and tell me what PCAP files are available.

Then analyze:
2014-11-08-traffic-analysis-exercise.pcap

Start with:
1. pcap_info
2. protocol_hierarchy
3. top_talkers
4. dns_queries

Do not modify the PCAP.
```

Claude should invoke the MCP tools instead of asking you to manually run TShark.

---

# Example Investigations

## List PCAPs

```text
List all available PCAP files.
```

Uses:

```text
list_pcaps
```

---

## PCAP Information

```text
Give me detailed metadata about the capture.
```

Uses:

```text
pcap_info
```

---

## DNS Investigation

```text
Find all DNS queries and identify the requested domains.
```

Uses:

```text
dns_queries
```

---

## HTTP Investigation

```text
Extract all HTTP requests including source IP,
destination IP, host, URI and User-Agent.
```

Uses:

```text
http_requests
```

---

## TCP Investigation

```text
Analyze TCP SYN, ACK, FIN and RST activity.
```

Uses:

```text
tcp_analysis
```

---

## Network Conversations

```text
Show me the main IP conversations in this capture.
```

Uses:

```text
conversations
```

---

## Display Filters

You can ask Claude to apply Wireshark display filters.

Example:

```text
Show packets where TCP reset is set.
```

Possible filter:

```text
tcp.flags.reset == 1
```

Or:

```text
Find HTTP requests to example.com.
```

The MCP server passes the display filter to TShark.

---

# Security Design

The server contains several restrictions intended to reduce unnecessary command/file access.

## PCAP Path Restriction

PCAP files must be located under:

```text
./pcaps
```

Absolute paths are rejected.

Path traversal is rejected.

For example:

```text
..\..\secret.pcap
```

is not accepted.

---

## File Extension Restriction

Only these extensions are accepted:

```text
.pcap
.pcapng
.cap
```

---

## No Shell Execution

TShark and capinfos are executed with:

```python
shell=False
```

The server uses fixed executable paths.

---

## Output Limits

The server limits:

```text
Maximum output: 200,000 characters
Maximum packets: 5,000
Command timeout: 120 seconds
```

These limits help prevent excessively large responses.

---

## Display Filter Validation

Display filters cannot be empty and are limited to:

```text
1000 characters
```

---

## Field Validation

Extracted Wireshark field names are restricted to:

```text
A-Z
a-z
0-9
_
.
-
```

Examples:

```text
ip.src
ip.dst
tcp.port
dns.qry.name
http.host
http.request.uri
```

---

# Project Structure

Final structure:

```text
MCP_SERVER/
│
├── .venv/
│   └── Python virtual environment
│
├── pcaps/
│   └── 2014-11-08-traffic-analysis-exercise.pcap
│
├── __pycache__/
│
└── server.py
```

---

# Troubleshooting

## `ModuleNotFoundError: No module named 'mcp'`

Make sure the virtual environment is activated:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then:

```powershell
python -m pip show mcp
```

If it isn't installed:

```powershell
python -m pip install mcp
```

---

## TShark says PCAP does not exist

Check:

```powershell
Get-ChildItem ".\pcaps"
```

The PCAP must be inside:

```text
C:\Users\Dharmesh\Desktop\MCP_SERVER\pcaps\
```

---

## Test TShark directly

```powershell
& "C:\Program Files\Wireshark\tshark.exe" -r ".\pcaps\YOUR_FILE.pcap" -c 5
```

---

## MCP server does not start

Run:

```powershell
python .\server.py
```

Check whether the following paths exist:

```powershell
Test-Path "C:\Program Files\Wireshark\tshark.exe"
Test-Path "C:\Program Files\Wireshark\capinfos.exe"
Test-Path ".\server.py"
Test-Path ".\pcaps"
```

All should return:

```text
True
```

---

## Claude cannot connect to the server

Verify that the Claude configuration points to:

```text
C:\Users\Dharmesh\Desktop\MCP_SERVER\.venv\Scripts\python.exe
```

and:

```text
C:\Users\Dharmesh\Desktop\MCP_SERVER\server.py
```

Then completely restart Claude Desktop.

Check Claude's logs if the connection still fails.

---

# Current Status

The following components have been successfully tested:

```text
Windows 11                  ✓
Python 3.13.3               ✓
Virtual environment         ✓
MCP SDK 2.2.0               ✓
Wireshark 4.6.9             ✓
TShark                      ✓
capinfos                     ✓
server.py                   ✓
Python compilation          ✓
MCP server startup          ✓
PCAP file                   ✓
PCAP parsing with TShark    ✓
```

The remaining integration step is:

```text
Claude Desktop
      ↓
Wireshark MCP Server
      ↓
TShark / capinfos
      ↓
PCAP analysis
```

---

# Example Workflow

A typical investigation can now look like:

```text
1. Claude
   │
   ├── list_pcaps
   │
   ├── pcap_info
   │
   ├── protocol_hierarchy
   │
   ├── top_talkers
   │
   ├── dns_queries
   │
   ├── http_requests
   │
   ├── tls_analysis
   │
   ├── tcp_analysis
   │
   └── suspicious_indicators
   │
   ▼
2. Claude correlates the results
   │
   ▼
3. Analyst investigates interesting traffic
```

The MCP server is intended to assist with **PCAP analysis and investigation**, while keeping the actual packet processing in Wireshark's TShark engine.
