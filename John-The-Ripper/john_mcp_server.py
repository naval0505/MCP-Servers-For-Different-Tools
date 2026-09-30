#!/usr/bin/env python3

"""
John the Ripper MCP Server

Exposes John the Ripper password auditing/cracking capabilities
through the Model Context Protocol (MCP).

Designed for MCP Python SDK 1.x, including 1.30.0.
"""

import asyncio
import os
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from typing import Any, Dict, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequestParams,
    CallToolResult,
    ListToolsResult,
    PaginatedRequestParams,
    TextContent,
    Tool,
)


class JohnMCPServer:
    """MCP server wrapper for John the Ripper."""

    def __init__(self):
        self.server = Server("john-the-ripper-mcp")
        self.john_path = self._find_john()
        self.setup_handlers()

    # ---------------------------------------------------------
    # John discovery
    # ---------------------------------------------------------

    def _find_john(self) -> Optional[str]:
        """Find the John the Ripper executable."""
        return shutil.which("john")

    def is_john_installed(self) -> bool:
        """Return True if John the Ripper is available."""
        return self.john_path is not None

    # ---------------------------------------------------------
    # Temporary hash file
    # ---------------------------------------------------------

    @contextmanager
    def temp_hash_file(self, hash_content: str):
        """Create and automatically remove a temporary hash file."""

        fd, temp_path = tempfile.mkstemp(
            suffix=".txt",
            prefix="hash_"
        )

        try:
            with os.fdopen(fd, "w") as f:
                f.write(hash_content)

            yield temp_path

        finally:
            try:
                os.remove(temp_path)
            except OSError:
                pass

    # ---------------------------------------------------------
    # Execute John
    # ---------------------------------------------------------

    def execute_john(
        self,
        args: str,
        timeout_sec: int = 30
    ) -> Dict[str, str]:

        if not self.is_john_installed():
            raise RuntimeError(
                "John the Ripper is not installed or not found in PATH."
            )

        command = [self.john_path] + self._split_command(args)

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                errors="replace",
            )

            return {
                "stdout": result.stdout or "",
                "stderr": result.stderr or "",
                "returncode": str(result.returncode),
            }

        except subprocess.TimeoutExpired:
            raise TimeoutError(
                f"John the Ripper timed out after {timeout_sec} seconds."
            )

        except Exception as e:
            raise RuntimeError(
                f"Error executing John the Ripper: {e}"
            )

    def _split_command(self, command: str):
        """
        Safely split a simple John argument string.

        shlex is used instead of shell=True so user-controlled
        arguments aren't executed through a shell.
        """
        import shlex
        return shlex.split(command)

    # ---------------------------------------------------------
    # MCP handlers
    # ---------------------------------------------------------

    def setup_handlers(self):

        @self.server.list_tools()
        async def list_tools(
            params: PaginatedRequestParams | None = None
        ) -> ListToolsResult:

            tools = [

                Tool(
                    name="john_crack_wordlist",
                    description=(
                        "Perform a wordlist password audit against a hash "
                        "using John the Ripper. Use only against hashes "
                        "you are authorized to test."
                    ),
                    input_schema={
                        "type": "object",
                        "properties": {

                            "hash": {
                                "type": "string",
                                "description": (
                                    "Password hash to audit."
                                ),
                            },

                            "wordlist": {
                                "type": "string",
                                "description": (
                                    "Path to a wordlist."
                                ),
                                "default": (
                                    "/usr/share/wordlists/rockyou.txt"
                                ),
                            },

                            "hash_type": {
                                "type": "string",
                                "description": (
                                    "John format, for example "
                                    "raw-md5, raw-sha1, raw-sha256, "
                                    "bcrypt. Leave as auto when possible."
                                ),
                                "default": "auto",
                            },

                            "max_run_time": {
                                "type": "integer",
                                "description": (
                                    "Maximum runtime in seconds."
                                ),
                                "default": 60,
                                "minimum": 1,
                                "maximum": 3600,
                            },

                        },

                        "required": ["hash"],
                    },
                ),

                Tool(
                    name="john_crack_brute_force",
                    description=(
                        "Perform a brute-force password audit using "
                        "John the Ripper. Use only against hashes "
                        "you are authorized to test."
                    ),
                    input_schema={
                        "type": "object",
                        "properties": {

                            "hash": {
                                "type": "string",
                                "description": (
                                    "Password hash to audit."
                                ),
                            },

                            "hash_type": {
                                "type": "string",
                                "description": "John hash format.",
                                "default": "auto",
                            },

                            "charset": {
                                "type": "string",
                                "description": (
                                    "Character set: lowercase, uppercase, "
                                    "digits, all, or a custom value."
                                ),
                                "default": "lowercase",
                            },

                            "min_length": {
                                "type": "integer",
                                "description": (
                                    "Minimum password length."
                                ),
                                "default": 1,
                                "minimum": 1,
                            },

                            "max_length": {
                                "type": "integer",
                                "description": (
                                    "Maximum password length."
                                ),
                                "default": 6,
                                "minimum": 1,
                            },

                            "max_run_time": {
                                "type": "integer",
                                "description": (
                                    "Maximum runtime in seconds."
                                ),
                                "default": 60,
                                "minimum": 1,
                                "maximum": 3600,
                            },

                        },

                        "required": ["hash"],
                    },
                ),

                Tool(
                    name="john_show_cracked",
                    description=(
                        "Show passwords previously recovered by "
                        "John the Ripper."
                    ),
                    input_schema={
                        "type": "object",
                        "properties": {

                            "hash_file": {
                                "type": "string",
                                "description": (
                                    "Path to the John hash file."
                                ),
                            },

                            "format": {
                                "type": "string",
                                "description": (
                                    "Optional John format filter."
                                ),
                            },

                        },

                        "required": ["hash_file"],
                    },
                ),

                Tool(
                    name="john_get_version",
                    description=(
                        "Get John the Ripper version and build information."
                    ),
                    input_schema={
                        "type": "object",
                        "properties": {},
                    },
                ),

                Tool(
                    name="john_list_formats",
                    description=(
                        "List supported John the Ripper hash formats."
                    ),
                    input_schema={
                        "type": "object",
                        "properties": {

                            "group": {
                                "type": "string",
                                "description": (
                                    "Optional format group filter, "
                                    "such as md5, sha, or crypt."
                                ),
                            },

                        },
                    },
                ),
            ]

            return ListToolsResult(tools=tools)

        # -----------------------------------------------------
        # Tool execution
        # -----------------------------------------------------

        @self.server.call_tool()
        async def call_tool(
            params: CallToolRequestParams
        ) -> CallToolResult:

            name = params.name
            arguments: Dict[str, Any] = params.arguments or {}

            try:

                if not self.is_john_installed():

                    return self.error_result(
                        "John the Ripper is not installed or not found in PATH."
                    )

                # ---------------------------------------------
                # WORDLIST
                # ---------------------------------------------

                if name == "john_crack_wordlist":

                    return self._crack_wordlist(arguments)

                # ---------------------------------------------
                # BRUTE FORCE
                # ---------------------------------------------

                elif name == "john_crack_brute_force":

                    return self._crack_brute_force(arguments)

                # ---------------------------------------------
                # SHOW CRACKED
                # ---------------------------------------------

                elif name == "john_show_cracked":

                    return self._show_cracked(arguments)

                # ---------------------------------------------
                # VERSION
                # ---------------------------------------------

                elif name == "john_get_version":

                    return self._get_version()

                # ---------------------------------------------
                # FORMATS
                # ---------------------------------------------

                elif name == "john_list_formats":

                    return self._list_formats(arguments)

                # ---------------------------------------------
                # UNKNOWN TOOL
                # ---------------------------------------------

                else:

                    return self.error_result(
                        f"Unknown tool: {name}"
                    )

            except Exception as e:

                return self.error_result(
                    f"Error executing {name}: {e}"
                )

    # ---------------------------------------------------------
    # Helper response
    # ---------------------------------------------------------

    @staticmethod
    def text_result(text: str) -> CallToolResult:

        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=text
                )
            ]
        )

    @staticmethod
    def error_result(text: str) -> CallToolResult:

        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"ERROR: {text}"
                )
            ],
            is_error=True,
        )

    # ---------------------------------------------------------
    # Wordlist attack
    # ---------------------------------------------------------

    def _crack_wordlist(
        self,
        args: Dict[str, Any]
    ) -> CallToolResult:

        hash_value = args.get("hash")

        if not hash_value:
            return self.error_result(
                "The 'hash' parameter is required."
            )

        wordlist = args.get(
            "wordlist",
            "/usr/share/wordlists/rockyou.txt"
        )

        hash_type = args.get(
            "hash_type",
            "auto"
        )

        max_run_time = int(
            args.get("max_run_time", 60)
        )

        if not os.path.isfile(wordlist):

            return self.error_result(
                f"Wordlist file not found: {wordlist}"
            )

        with self.temp_hash_file(hash_value) as hash_file:

            cmd = []

            if hash_type and hash_type != "auto":
                cmd.append(f"--format={hash_type}")

            cmd.extend([
                hash_file,
                f"--wordlist={wordlist}",
                f"--max-run-time={max_run_time}",
            ])

            result = self.execute_john(
                " ".join(
                    self._quote(x)
                    for x in cmd
                ),
                max_run_time + 10,
            )

        output = (
            result["stdout"]
            or result["stderr"]
            or "John completed without output."
        )

        return self.text_result(
            "Wordlist attack completed.\n\n" + output
        )

    # ---------------------------------------------------------
    # Brute force
    # ---------------------------------------------------------

    def _crack_brute_force(
        self,
        args: Dict[str, Any]
    ) -> CallToolResult:

        hash_value = args.get("hash")

        if not hash_value:
            return self.error_result(
                "The 'hash' parameter is required."
            )

        hash_type = args.get(
            "hash_type",
            "auto"
        )

        charset = args.get(
            "charset",
            "lowercase"
        )

        min_length = int(
            args.get("min_length", 1)
        )

        max_length = int(
            args.get("max_length", 6)
        )

        max_run_time = int(
            args.get("max_run_time", 60)
        )

        if min_length < 1:
            return self.error_result(
                "min_length must be at least 1."
            )

        if max_length < min_length:
            return self.error_result(
                "max_length must be greater than or equal to min_length."
            )

        charset_map = {
            "lowercase": "a:z",
            "uppercase": "A:Z",
            "digits": "0:9",
            "all": "a:zA:Z0:9",
        }

        john_charset = charset_map.get(
            charset,
            charset
        )

        with self.temp_hash_file(hash_value) as hash_file:

            cmd = []

            if hash_type and hash_type != "auto":
                cmd.append(f"--format={hash_type}")

            cmd.extend([
                hash_file,
                "--incremental=charset",
                f"--max-run-time={max_run_time}",
            ])

            # NOTE:
            # John incremental mode uses its own charset configuration.
            # The original implementation calculated john_charset but
            # did not actually use it either.
            #
            # We preserve that behavior rather than pretending that
            # --incremental accepts an arbitrary charset directly.

            result = self.execute_john(
                " ".join(
                    self._quote(x)
                    for x in cmd
                ),
                max_run_time + 10,
            )

        output = (
            result["stdout"]
            or result["stderr"]
            or "John completed without output."
        )

        return self.text_result(
            "Brute-force audit completed.\n\n"
            f"Requested charset: {charset}\n"
            f"Length range: {min_length}-{max_length}\n\n"
            f"{output}"
        )

    # ---------------------------------------------------------
    # Show cracked
    # ---------------------------------------------------------

    def _show_cracked(
        self,
        args: Dict[str, Any]
    ) -> CallToolResult:

        hash_file = args.get("hash_file")

        if not hash_file:
            return self.error_result(
                "The 'hash_file' parameter is required."
            )

        format_filter = args.get(
            "format",
            ""
        )

        cmd = ["--show"]

        if format_filter:
            cmd.append(
                f"--format={format_filter}"
            )

        cmd.append(hash_file)

        result = self.execute_john(
            " ".join(
                self._quote(x)
                for x in cmd
            ),
            10,
        )

        output = (
            result["stdout"]
            or result["stderr"]
            or "No cracked passwords found."
        )

        return self.text_result(output)

    # ---------------------------------------------------------
    # Version
    # ---------------------------------------------------------

    def _get_version(self) -> CallToolResult:

        version_result = self.execute_john(
            "--version",
            5,
        )

        try:

            build_result = self.execute_john(
                "--list=build-options",
                5,
            )

            build_info = (
                build_result["stdout"]
                or build_result["stderr"]
            )

        except Exception:

            build_info = (
                "Build options not available."
            )

        output = (
            version_result["stdout"]
            or version_result["stderr"]
        )

        return self.text_result(
            f"{output}\n\n"
            f"Build Options:\n{build_info}"
        )

    # ---------------------------------------------------------
    # List formats
    # ---------------------------------------------------------

    def _list_formats(
        self,
        args: Dict[str, Any]
    ) -> CallToolResult:

        group = args.get("group")

        if group:

            # Use John's own filtering rather than shelling out
            # to grep.
            result = self.execute_john(
                "--list=formats",
                10,
            )

            formats = [
                line.strip()
                for line in result["stdout"].splitlines()
                if line.strip()
                and group.lower() in line.lower()
            ]

        else:

            result = self.execute_john(
                "--list=formats",
                10,
            )

            formats = [
                line.strip()
                for line in result["stdout"].splitlines()
                if line.strip()
            ]

        formats = formats[:50]

        if not formats:

            return self.text_result(
                "No matching hash formats found."
            )

        return self.text_result(
            "Supported Hash Formats:\n\n"
            + "\n".join(formats)
            + "\n\n"
            "(Showing first 50 results.)"
        )

    # ---------------------------------------------------------
    # Simple quoting helper
    # ---------------------------------------------------------

    @staticmethod
    def _quote(value: str) -> str:

        import shlex

        return shlex.quote(str(value))

    # ---------------------------------------------------------
    # Run MCP server
    # ---------------------------------------------------------

    async def run(self):

        async with stdio_server() as (
            read_stream,
            write_stream
        ):

            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


# =============================================================
# Main
# =============================================================

async def main():

    server = JohnMCPServer()

    await server.run()


if __name__ == "__main__":

    asyncio.run(main())
