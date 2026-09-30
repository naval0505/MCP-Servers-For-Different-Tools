# 🛠️ MCP Servers Collection

A collection of powerful [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) servers designed to extend Claude and other AI assistants with specialized tools and capabilities.

## 📋 Overview

This repository contains a curated collection of MCP servers built for Claude Desktop and other MCP-compatible applications. Each server is designed with security, performance, and ease of integration in mind.

### What are MCP Servers?

MCP (Model Context Protocol) servers enable AI assistants to:
- Access external tools and services
- Perform specialized tasks and computations
- Interact with APIs and databases
- Execute security-related operations
- Process data and files
- Automate workflows

## 📦 Servers in This Collection

### 1. **John the Ripper MCP Server** 🔐
A Python-based MCP server providing password cracking and hash analysis capabilities.

**Features:**
- Hash cracking with John the Ripper
- Support for multiple hash formats
- Dictionary and brute-force attacks
- Real-time progress tracking
- Configurable wordlists

**Installation:**
```bash
pip install -r john-mcp-server/requirements.txt
python john-mcp-server/server.py
```

**Available Tools:**
- `crack_hash` - Crack password hashes
- `identify_hash` - Identify hash types
- `wordlist_analysis` - Analyze wordlist strength
- `benchmark` - Run performance benchmarks
- `status_check` - Check server status

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Claude Desktop or compatible MCP client
- Git

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/naval0505/mcp-servers.git
cd mcp-servers
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure Claude Desktop:**
Add to `~/.claude_desktop_config` (macOS/Linux) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "john-mcp": {
      "command": "python",
      "args": ["/path/to/mcp-servers/john-mcp-server/server.py"]
    }
  }
}
```

4. **Restart Claude Desktop**

## 🔧 Architecture

Each server follows the standard MCP protocol structure:

```
server-name/
├── server.py           # Main server implementation
├── requirements.txt    # Python dependencies
├── config.json        # Server configuration
├── tools/             # Tool implementations
├── utils/             # Utility functions
├── tests/             # Unit tests
└── README.md          # Server-specific documentation
```

## 📚 Usage Examples

### Using John the Ripper Server

```python
# Crack a hash
result = await client.call_tool(
    "crack_hash",
    {
        "hash": "5d41402abc4b2a76b9719d911017c592",
        "hash_type": "md5",
        "wordlist": "rockyou.txt"
    }
)
```

## 🔒 Security Considerations

- ⚠️ **Use responsibly**: These tools are for authorized security testing only
- 🔐 **Authentication**: Implement proper authentication for sensitive operations
- 🛡️ **Rate limiting**: Configure rate limits to prevent abuse
- 📝 **Logging**: Enable comprehensive logging for audit trails
- 🚫 **Validation**: All inputs are sanitized and validated

## 🛠️ Development

### Creating a New Server

1. Create a new directory: `your-server-name/`
2. Copy the template structure from an existing server
3. Implement your tools following the MCP protocol
4. Add comprehensive tests
5. Write documentation
6. Submit a pull request

### Testing

```bash
pytest tests/
```

### Code Quality

```bash
black .
flake8 .
mypy .
```

## 📖 Documentation

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Claude Desktop Documentation](https://claude.ai/docs)
- Individual server READMEs in each server directory

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-server`)
3. Commit changes (`git commit -am 'Add amazing server'`)
4. Push to the branch (`git push origin feature/amazing-server`)
5. Open a Pull Request

### Contribution Guidelines
- Follow PEP 8 style guide
- Write comprehensive tests
- Include documentation
- Test security implications
- Update this README with new servers

## 📋 Requirements

Each server may have different requirements. Check individual server documentation for specifics.

**Common Requirements:**
- Python 3.8+
- pip (Python package manager)
- Git
- Terminal/Command Prompt access

**Server-Specific Requirements:**
- **John the Ripper Server**: John the Ripper installation, wordlists

## 🐛 Troubleshooting

### Server not connecting to Claude Desktop
- Verify the path in `claude_desktop_config.json` is absolute
- Check Python version compatibility
- Ensure all dependencies are installed
- Review server logs for errors

### Tools not appearing in Claude
- Restart Claude Desktop after configuration changes
- Verify tool names match exactly
- Check server console for initialization errors

### Performance issues
- Monitor server resource usage
- Check for long-running processes
- Consider implementing timeouts
- Review logs for bottlenecks

## 📄 License

This repository is licensed under the [MIT License](LICENSE).

## 👤 Author

**Kabir** - Red Team Security Expert  
GitHub: [@naval0505](https://github.com/naval0505)

## 🔗 Links

- [GitHub Repository](https://github.com/naval0505/mcp-servers)
- [MCP Official Website](https://modelcontextprotocol.io/)
- [Claude Documentation](https://claude.ai/docs)
- [John the Ripper](https://www.openwall.com/john/)

## 💡 Roadmap

- [ ] Metasploit MCP Server
- [ ] Nessus Scanner Integration
- [ ] OWASP ZAP MCP Server
- [ ] Wireshark Network Analysis Server
- [ ] Burp Suite Integration
- [ ] Custom payload generator
- [ ] Log analysis and forensics server
- [ ] Network reconnaissance tools
- [ ] Vulnerability database server
- [ ] Automated reporting system

## ⚡ Support

For issues, questions, or suggestions:
- Open an [Issue](https://github.com/naval0505/mcp-servers/issues)
- Check existing documentation
- Review server-specific troubleshooting guides

---

**Made with 🔒 for the cybersecurity community**

*Last Updated: 2026*
