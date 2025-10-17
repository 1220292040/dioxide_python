# Dioxide Python SDK

Python SDK for interacting with Dioxide blockchain network.

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Features

- **Account Management**: Create and manage Ed25519 accounts
- **Transaction Operations**: Send, compose, and sign transactions
- **Contract Deployment**: Deploy and interact with smart contracts
- **State Queries**: Query on-chain state and contract information
- **Real-time Subscriptions**: Subscribe to blockchain events via WebSocket
- **DApp Management**: Create and manage decentralized applications
- **Token Operations**: Mint, transfer, and manage tokens

## Quick Start

### Setup

```bash
# Clone repository
git clone https://github.com/1220292040/dioxide_python.git
cd dioxide_python

# Install dependencies
make install
```

This sets up the development environment and installs all dependencies via Poetry.

### Basic Usage

```python
from dioxide_python_sdk.client.dioxclient import DioxClient
from dioxide_python_sdk.client.account import DioxAccount

# Connect to node
client = DioxClient()

# Create account
account = DioxAccount.generate_key_pair()

# Get chain info
overview = client.get_overview()
print(f"Block height: {overview['HeadHeight']}")
```

## Documentation

- [Quick Start Guide](doc/QUICKSTART.md) - Setup and getting started tutorial
- [API Reference](doc/API_REFERENCE.md) - Complete API documentation

## Project Structure

```
dioxide_python/
├── dioxide_python_sdk/   # SDK source code
│   ├── client/          # Client and account management
│   ├── config/          # Configuration
│   └── utils/           # Utility functions
├── tests/               # Test scripts
├── doc/                 # Documentation
├── demo.py              # Demo script
└── Makefile             # Build automation
```

## Development

```bash
# Run demo
make demo

# Run tests
make test

# Clean project
make clean
```

## Requirements

- Python 3.9+
- Poetry (for dependency management)
- Running Dioxide node

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License

## Links

- [GitHub Repository](https://github.com/1220292040/dioxide_python)
- [Dioxide Documentation](https://dioxide.network)

## Support

For issues and questions:
- Open an issue on [GitHub](https://github.com/1220292040/dioxide_python/issues)
- Check existing [documentation](doc/)
