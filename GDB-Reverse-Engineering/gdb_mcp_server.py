#!/usr/bin/env python3

import subprocess
from pathlib import Path

from fastmcp import FastMCP


mcp = FastMCP("gdb-mcp")


def run_gdb(binary: str, commands: list[str]) -> str:
    path = Path(binary).expanduser().resolve()

    if not path.exists():
        return f"Error: file does not exist: {path}"

    cmd = [
        "/usr/bin/gdb",
        "-q",
        "-nx",
        "-batch",
        str(path),
    ]

    for command in commands:
        cmd.extend(["-ex", command])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout

        if result.stderr:
            output += "\n" + result.stderr

        return output.strip()

    except subprocess.TimeoutExpired:
        return "Error: GDB command timed out."

    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def gdb_info(binary: str) -> str:
    """Show basic information about a binary using GDB."""
    return run_gdb(
        binary,
        [
            "info files",
            "show architecture",
            "show endian",
            "show osabi",
        ],
    )


@mcp.tool()
def disassemble(binary: str, function: str) -> str:
    """Disassemble a function using Intel syntax."""
    return run_gdb(
        binary,
        [
            "set disassembly-flavor intel",
            f"disassemble {function}",
        ],
    )


@mcp.tool()
def registers(binary: str) -> str:
    """Show CPU register information."""
    return run_gdb(
        binary,
        [
            "info registers",
        ],
    )


@mcp.tool()
def functions(binary: str) -> str:
    """List functions known to GDB."""
    return run_gdb(
        binary,
        [
            "info functions",
        ],
    )


@mcp.tool()
def shared_libraries(binary: str) -> str:
    """Show shared libraries associated with the binary."""
    return run_gdb(
        binary,
        [
            "info sharedlibrary",
        ],
    )


@mcp.tool()
def sections(binary: str) -> str:
    """Show binary sections."""
    return run_gdb(
        binary,
        [
            "maintenance info sections",
        ],
    )


@mcp.tool()
def entry_point(binary: str) -> str:
    """Show the binary entry point and disassemble _start."""
    return run_gdb(
        binary,
        [
            "info files",
            "info address _start",
            "disassemble _start",
        ],
    )


@mcp.tool()
def function_address(binary: str, function: str) -> str:
    """Find the address of a function."""
    return run_gdb(
        binary,
        [
            f"info address {function}",
            f"p/x &{function}",
        ],
    )


@mcp.tool()
def read_memory(
    binary: str,
    address: str,
    count: int = 16,
) -> str:
    """Read memory from an address in hexadecimal."""
    count = max(1, min(count, 200))

    return run_gdb(
        binary,
        [
            f"x/{count}gx {address}",
        ],
    )


@mcp.tool()
def strings_at(
    binary: str,
    address: str,
) -> str:
    """Read a string from a memory address."""
    return run_gdb(
        binary,
        [
            f"x/s {address}",
        ],
    )


@mcp.tool()
def stack(binary: str, count: int = 32) -> str:
    """Display stack memory."""
    count = max(1, min(count, 200))

    return run_gdb(
        binary,
        [
            f"x/{count}gx $rsp",
        ],
    )


@mcp.tool()
def breakpoint_info(binary: str, location: str) -> str:
    """Inspect a breakpoint location without executing the binary."""
    return run_gdb(
        binary,
        [
            f"break {location}",
            "info breakpoints",
        ],
    )


@mcp.tool()
def evaluate(binary: str, expression: str) -> str:
    """Evaluate a GDB expression without running the target."""
    return run_gdb(
        binary,
        [
            f"print {expression}",
        ],
    )


@mcp.tool()
def evaluate_hex(binary: str, expression: str) -> str:
    """Evaluate a GDB expression and display it in hexadecimal."""
    return run_gdb(
        binary,
        [
            f"print/x {expression}",
        ],
    )


@mcp.tool()
def disassemble_address(
    binary: str,
    address: str,
    count: int = 20,
) -> str:
    """Disassemble instructions starting at an address."""
    count = max(1, min(count, 200))

    return run_gdb(
        binary,
        [
            "set disassembly-flavor intel",
            f"x/{count}i {address}",
        ],
    )


@mcp.tool()
def triage(binary: str) -> str:
    """Perform basic read-only GDB triage of a binary."""
    return run_gdb(
        binary,
        [
            "set pagination off",
            "set disassembly-flavor intel",
            "info files",
            "show architecture",
            "show endian",
            "show osabi",
            "info sharedlibrary",
            "info address main",
            "info address _start",
            "info functions",
        ],
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
