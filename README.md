# Sophos Partner CLI

A Python command-line interface tool for managing Sophos Partner accounts using the Sophos Central APIs. This tool allows you to view tenants and endpoints with clean, formatted output and automatic CSV export.

## Features

- **List All Tenants**: Display all tenants under your partner account with their details
- **List All Endpoints**: View all active endpoints across all tenants, including hostname, OS, and OS version
- **Beautiful CLI Interface**: Clean, colorful output using the Rich library
- **CSV Export**: Automatically export results to timestamped CSV files
- **Pagination Support**: Automatically handles API pagination for large datasets

## Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer
- Sophos Partner account with API credentials

## Installation

### 1. Install uv (if not already installed)

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Clone the repository

```bash
git clone <your-repository-url>
cd Sophos
```

### 3. Create a virtual environment and install dependencies

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

## Configuration

### Obtaining Sophos API Credentials

1. Log in to your [Sophos Central Partner](https://cloud.sophos.com/) dashboard
2. Navigate to **Settings & Policies** > **API Credentials Management**
3. Click **Add Credential**
4. Select appropriate permissions (at minimum: read access to tenants and endpoints)
5. Save your **Client ID** and **Client Secret**

### Setting up Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and add your credentials:
   ```
   SOPHOS_CLIENT_ID=your_client_id_here
   SOPHOS_CLIENT_SECRET=your_client_secret_here
   ```

**Important:** Never commit your `.env` file to version control. It's already included in `.gitignore`.

## Usage

### Running the CLI

With your virtual environment activated:

```bash
python -m sophos_cli.main
```

Or if you installed the package:

```bash
sophos-cli
```

### Menu Options

The CLI provides an interactive menu with the following options:

#### 1. List All Tenants
- Displays a formatted table of all tenants under your partner account
- Shows: Tenant Name, Tenant ID, Data Region, and Status
- Exports data to `output/sophos_tenants_YYYYMMDD_HHMMSS.csv`

#### 2. List All Endpoints (Active)
- Retrieves all endpoints across all tenants
- Shows: Tenant Name, Hostname, OS, and OS Build Version
- Exports data to `output/sophos_endpoints_YYYYMMDD_HHMMSS.csv`
- Note: This may take a moment for accounts with many tenants/endpoints

#### 3. Show Account Health for All Tenants
- Displays account health check scores for all tenants
- Shows: Overall Score, Status, Protection Score, Policy Score, Exclusions Score, and Tamper Protection Score
- Exports data to `output/sophos_tenant_health_YYYYMMDD_HHMMSS.csv`
- Note: This may take a moment for accounts with many tenants

#### 4. Exit
- Closes the application

## Project Structure

```
Sophos/
├── .env                    # Your API credentials (not in git)
├── .env.example           # Template for environment variables
├── .gitignore             # Git ignore rules
├── README.md              # This file
├── pyproject.toml         # Project dependencies and metadata
├── output/                # CSV export directory (auto-created)
└── sophos_cli/
    ├── __init__.py        # Package initialization
    ├── main.py            # CLI interface and menu
    ├── api_client.py      # Sophos API client
    └── utils.py           # Utility functions (CSV export)
```

## API Documentation

This tool uses the following Sophos APIs:

- **Authentication**: [OAuth2 Token](https://developer.sophos.com/intro)
- **Partner API**: [Get Tenants](https://developer.sophos.com/docs/partner-v1/1/routes/tenants/get)
- **Endpoint API**: [Get Endpoints](https://developer.sophos.com/docs/endpoint-v1/1/routes/endpoints/get)
- **Account Health Check API**: [Health Check](https://developer.sophos.com/account-health-check)

## Development

### Installing in Development Mode

```bash
uv pip install -e .
```

### Running Tests

(To be implemented)

```bash
pytest
```

## Troubleshooting

### "Missing API credentials" Error
- Ensure your `.env` file exists and contains valid credentials
- Check that `SOPHOS_CLIENT_ID` and `SOPHOS_CLIENT_SECRET` are set correctly

### "This tool requires a partner account" Error
- Verify that you're using credentials from a Sophos Partner account, not an organization account

### API Rate Limiting
- The tool includes automatic pagination but does not currently implement rate limiting
- If you encounter rate limit errors, wait a few moments before retrying

### Connection Errors
- Verify your internet connection
- Check that you can access `https://id.sophos.com` and `https://api.central.sophos.com`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Support

For issues related to:
- **This tool**: Open an issue in this repository
- **Sophos APIs**: Visit the [Sophos Developer Portal](https://developer.sophos.com/)
- **Sophos Central**: Contact [Sophos Support](https://support.sophos.com/)
