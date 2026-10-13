# MobSF MCP Server for Claude Desktop

A Model Context Protocol (MCP) server that connects the Mobile Security Framework (MobSF) to Claude Desktop, enabling AI-assisted mobile application security analysis through MobSF's REST API.

The server runs using system Python on Kali Linux without requiring a Python virtual environment. MobSF runs independently in Docker.

## Features

- **MobSF Connectivity:** Check whether the MobSF web service is reachable.
- **APK Upload and Scanning:** Upload supported application files and initiate static analysis.
- **JSON Reports:** Retrieve detailed MobSF analysis reports.
- **Scan Search:** Search existing scans by filename, package name, or hash.
- **Recent Scans:** Retrieve the list of recent MobSF scans.
- **Scan Logs:** Access logs associated with a particular scan.
- **PDF Reports:** Download analysis reports to a local directory.
- **Claude Desktop Integration:** Expose MobSF operations as MCP tools.
- **No Virtual Environment:** Use the existing system Python installation.

## Architecture

```text
Claude Desktop
      |
      | MCP (stdio)
      v
MobSF MCP Server
      |
      | HTTP REST API
      v
MobSF Docker Container
      |
      v
Mobile Application Security Analysis
      |
      v
JSON Reports / PDF Reports
```

## Requirements

- Kali Linux
- Python 3
- FastMCP Python package
- Docker
- MobSF running in Docker
- MobSF API key
- Claude Desktop with MCP support

## Project Structure

```text
/home/kali/mcp/android/
├── mobsf_mcp.py
├── README.md
└── mobsf_reports/
    └── <scan-hash>.pdf
```

The `mobsf_reports` directory is created when a PDF report is downloaded.

## Installation

### 1. Verify Docker and MobSF

Check whether the MobSF container is running:

```bash
docker ps
```

Confirm the MobSF web interface is reachable at:

```text
http://127.0.0.1:8000
```

If MobSF uses a different host port, update the URL in the configuration accordingly.

### 2. Verify Python

```bash
python3 --version
```

### 3. Install FastMCP

If FastMCP is not already installed in the system Python environment:

```bash
sudo python3 -m pip install fastmcp
```

Kali Linux may prevent system-wide pip installations because of its externally managed Python environment. Do not force an installation with `--break-system-packages` on a production system. Use Kali's available package or managed installation method if required.

### 4. Create the project directory

```bash
mkdir -p /home/kali/mcp/android
cd /home/kali/mcp/android
```

Save the MCP server code as:

```text
mobsf_mcp.py
```

Set appropriate permissions:

```bash
chmod 700 mobsf_mcp.py
```

## Configuration

### MobSF API Key

The MCP server authenticates requests using the MobSF API key in the HTTP `Authorization` header.

Retrieve the API key using your installed MobSF version's interface or documentation.

Set the environment variables in a Kali shell for manual testing:

```bash
export MOBSF_URL="http://127.0.0.1:8000"
read -rsp "MobSF API key: " MOBSF_API_KEY
echo
export MOBSF_API_KEY
```

The key should be treated as a secret and should not be committed to a public repository.

### Environment Variables

| Variable | Description | Default |
|---|---|---|
| `MOBSF_URL` | MobSF base URL | `http://127.0.0.1:8000` |
| `MOBSF_API_KEY` | MobSF API authentication key | Not set |
| `MOBSF_REPORT_DIR` | Destination for PDF reports | `/home/kali/mcp/android/mobsf_reports` |

## Available MCP Tools

| Tool | Description |
|---|---|
| `mobsf_status` | Check MobSF service availability |
| `mobsf_upload_and_scan` | Upload a file and initiate static analysis |
| `mobsf_get_json_report` | Retrieve a JSON analysis report |
| `mobsf_search` | Search existing MobSF scans |
| `mobsf_recent_scans` | List recent scans |
| `mobsf_scan_logs` | Retrieve scan logs |
| `mobsf_download_pdf_report` | Download a PDF report locally |

## Claude Desktop Setup

Add the following entry to Claude Desktop's MCP configuration. Replace `YOUR_MOBSF_API_KEY` with your actual MobSF API key.

```json
{
  "mcpServers": {
    "mobsf": {
      "command": "/usr/bin/python3",
      "args": [
        "/home/kali/mcp/android/mobsf_mcp.py"
      ],
      "env": {
        "MOBSF_URL": "http://127.0.0.1:8000",
        "MOBSF_API_KEY": "YOUR_MOBSF_API_KEY",
        "MOBSF_REPORT_DIR": "/home/kali/mcp/android/mobsf_reports"
      }
    }
  }
}
```

Save the configuration and restart Claude Desktop.

**Important:** If Claude Desktop runs on Windows while MobSF and the MCP server run inside a separate Kali Linux VM, the configuration above needs a remote connection. The Windows application cannot directly execute `/usr/bin/python3` inside the VM, and `127.0.0.1` refers to the Windows host.

## Running the Server Manually

Run the MCP server from Kali Linux:

```bash
cd /home/kali/mcp/android
python3 mobsf_mcp.py
```

The server uses standard input/output (stdio) for MCP communication. When launched by Claude Desktop, it is managed by the desktop client. Avoid printing diagnostic messages directly to standard output, because that stream is used for MCP protocol communication.

## Usage Examples

After connecting the MCP server, you can ask Claude Desktop to:

- Check whether MobSF is reachable.
- Upload an authorized APK and initiate static analysis.
- Retrieve and summarize findings from a scan report.
- Search previous scans using a package name or hash.
- Retrieve logs for a particular scan.
- Save a PDF report to the configured reports directory.

Example prompt:

> Check the MobSF service, analyze the APK at `/home/kali/mcp/android/sample.apk`, and summarize the important security findings from its report.

## Troubleshooting

### MobSF Is Unreachable

Check the container:

```bash
docker ps
```

Check the web service:

```bash
curl -I http://127.0.0.1:8000
```

Verify the configured host port and MobSF container status.

### API Authentication Fails

- Verify the API key.
- Confirm that `MOBSF_API_KEY` is available to the MCP process.
- Check the MobSF logs for authentication or API errors.

### MCP Server Does Not Start

Verify the Python dependency:

```bash
python3 -c "import fastmcp; print('FastMCP OK')"
```

Run the server manually to check for startup errors:

```bash
python3 /home/kali/mcp/android/mobsf_mcp.py
```

### Claude Desktop Does Not Connect

- Verify the Python executable path.
- Verify the absolute path to `mobsf_mcp.py`.
- Validate the JSON configuration.
- Restart Claude Desktop.
- Check Claude Desktop's MCP logs for connection errors.
- If using a separate VM, configure an appropriate remote transport.

## Security Considerations

- Use this server only for applications you are authorized to assess.
- Keep the MobSF API key private.
- Do not expose the MobSF API or web interface publicly without appropriate access controls.
- Restrict access to the host and Docker network.
- Review the handling of uploaded applications and generated reports.
- Treat analysis results as security indicators that require validation, not as definitive proof of exploitability.

## Scope and Limitations

This project currently provides an MCP interface to selected MobSF REST API operations.

- Static analysis is supported through the upload and scan workflow.
- JSON reports, scan searches, logs, and PDF reports are supported through the implemented tools.
- Dynamic analysis orchestration is not included in the current implementation.
- MobSF API endpoint behavior may vary between versions.
- The MCP server requires a reachable MobSF service and a valid API key for authenticated operations.

## License

Choose and add a license before distributing this project publicly. Review the licensing requirements of MobSF and all included dependencies separately.

## Disclaimer

This project is intended for authorized mobile application security testing, research, and educational purposes. Users are responsible for complying with applicable laws, policies, and authorization requirements.

## JAI SHRI RAM
