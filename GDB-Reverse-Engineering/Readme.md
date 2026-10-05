# GDB MCP Server

An MCP (Model Context Protocol) server that connects **Claude Desktop** with **GDB (GNU Debugger)** for AI-assisted binary analysis and reverse engineering.

The server exposes GDB functionality as MCP tools, allowing an AI assistant to inspect binaries, analyze assembly, examine registers and memory, investigate functions, inspect shared libraries, and perform other read-oriented debugging and reverse-engineering tasks.

## Features

The GDB MCP Server provides tools for:

- Binary and GDB information
- Assembly/disassembly analysis
- CPU register inspection
- Function enumeration
- Function address lookup
- Shared library inspection
- Binary section inspection
- Entry-point identification
- Memory inspection
- String inspection at memory addresses
- Stack inspection
- Breakpoint information
- GDB expression evaluation
- Hexadecimal/address evaluation
- Disassembly from specific addresses
- Automated binary triage

## Use Cases

This MCP server can be useful for:

### Reverse Engineering

Analyze executable files and understand their internal structure and execution flow.

### Malware Analysis

Assist with initial binary triage, inspect suspicious functions, examine imported/shared libraries, and analyze assembly instructions.

### CTF and Binary Challenges

Use Claude as an AI-assisted interface for examining binaries, functions, memory, registers, and assembly.

### Vulnerability Research

Inspect program execution, memory regions, functions, stack information, and low-level program behavior.

### Binary Triage

Quickly gather useful information about an unknown executable before performing deeper analysis.

### Debugging

Use GDB through Claude to inspect program state and understand low-level behavior.

## Architecture

```text
┌─────────────────────┐
│    Claude Desktop   │
└──────────┬──────────┘
           │
           │ MCP / stdio
           ▼
┌─────────────────────┐
│    GDB MCP Server   │
│      Python         │
└──────────┬──────────┘
           │
           │ GDB commands
           ▼
┌─────────────────────┐
│         GDB         │
│   GNU Debugger      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│       Binary        │
│ ELF / Executable    │
└─────────────────────┘
```

## Requirements

- Linux system
- Python 3
- GDB
- Claude Desktop
- FastMCP
- MCP Python SDK

The server is designed to work with the system Python installation and does **not require a Python virtual environment**.

## Installation

### 1. Install GDB

On Kali Linux:

```bash
sudo apt update
sudo apt install gdb
```

Verify:

```bash
gdb --version
```

You should have GDB available at:

```text
/usr/bin/gdb
```

### 2. Install Python dependencies

Install FastMCP and the MCP Python SDK system-wide:

```bash
python -m pip install -U fastmcp mcp --break-system-packages
```

If Kali's existing `typing-extensions` package causes an installation conflict, use:

```bash
/usr/bin/python -m pip install --break-system-packages --ignore-installed typing-extensions
```

Then:

```bash
/usr/bin/python -m pip install --break-system-packages --ignore-installed fastmcp mcp
```

Verify the imports:

```bash
/usr/bin/python -c "import fastmcp; import mcp; print('IMPORTS OK')"
```

## Configuration

Place the server somewhere permanent, for example:

```text
/home/kali/mcp/gdb/gdb_server.py
```

Make sure the file exists:

```bash
ls -l /home/kali/mcp/gdb/gdb_server.py
```

## Claude Desktop Configuration

Open the Claude Desktop configuration file and add:

```json
{
  "mcpServers": {
    "gdb-mcp": {
      "command": "/usr/bin/python",
      "args": [
        "/home/kali/mcp/gdb/gdb_server.py"
      ]
    }
  }
}
```

### Important

The path in `args` must point to the actual location of `gdb_server.py`.

For example, if the server is located at:

```text
/home/kali/mcp/gdb/gdb_server.py
```

then Claude must use exactly that path.

## Testing the Server

Before connecting it to Claude Desktop, test the server directly:

```bash
/usr/bin/python /home/kali/mcp/gdb/gdb_server.py
```

If the MCP server starts successfully, it is ready to be connected to Claude Desktop.

## Example Workflow

Start with an executable:

```text
./sample
```

Claude can then use the MCP server to perform tasks such as:

```text
Analyze this binary and give me a basic triage.
```

```text
Find the entry point and disassemble it.
```

```text
List the functions in this binary.
```

```text
Show me the shared libraries used by this executable.
```

```text
Find the address of main and disassemble it.
```

```text
Show me the CPU registers.
```

```text
Inspect the stack around the current frame.
```

```text
Read memory at this address.
```

```text
Find interesting functions related to authentication.
```

## Available MCP Tools

| Tool | Purpose |
|---|---|
| `gdb_info` | Retrieve basic GDB/binary information |
| `disassemble` | Disassemble functions |
| `registers` | Inspect CPU registers |
| `functions` | List functions |
| `shared_libraries` | Inspect loaded/shared libraries |
| `sections` | Inspect binary sections |
| `entry_point` | Identify the executable entry point |
| `function_address` | Find the address of a function |
| `read_memory` | Read memory from an address |
| `strings_at` | Inspect strings at a memory location |
| `stack` | Inspect stack information |
| `breakpoint_info` | Inspect breakpoint information |
| `evaluate` | Evaluate GDB expressions |
| `evaluate_hex` | Evaluate hexadecimal values/addresses |
| `disassemble_address` | Disassemble from a specific address |
| `triage` | Perform basic binary triage |

## Security Considerations

This project is intended for **authorized security research, reverse engineering, malware analysis, debugging, CTFs, and educational purposes**.

Use it only on binaries and systems that you are authorized to analyze.

The MCP server is designed primarily around inspection and analysis functionality. It should not be treated as a sandbox or security boundary.

Running GDB against an untrusted executable can have security implications depending on how the binary and debugging environment are configured.

For malware analysis, use an appropriately isolated environment such as a dedicated VM or sandbox.

## Why MCP?

Without MCP, an AI assistant cannot directly interact with GDB in a structured way.

This project exposes GDB functionality through MCP tools:

```text
Claude
   │
   ├── gdb_info
   ├── disassemble
   ├── functions
   ├── registers
   ├── sections
   ├── shared_libraries
   ├── read_memory
   ├── stack
   └── triage
          │
          ▼
        GDB
          │
          ▼
       Binary
```

This allows Claude to act as an **AI-assisted reverse-engineering interface** instead of requiring the analyst to manually execute every GDB command.

## Project Goals

The goal of this project is to make low-level binary analysis more accessible through an AI interface while keeping the underlying analysis capabilities of GDB.

Potential future improvements include:

- More advanced breakpoint management
- Watchpoint support
- Better ELF analysis
- Symbol analysis
- Automated function analysis
- Calling-convention analysis
- Improved memory mapping analysis
- Integration with additional reverse-engineering tools
- More advanced binary triage
- Better support for debugging workflows

## Disclaimer

This project is provided for educational and authorized security research purposes.

Do not use it to analyze systems, applications, or binaries without appropriate authorization.

## License

Add your preferred license here.

For example:

```text
MIT License
```

---

## Author

Built as part of an MCP-based security tooling project focused on integrating AI assistants with cybersecurity and reverse-engineering workflows.
