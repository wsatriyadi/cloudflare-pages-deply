# Cloudflare Pages Deployment Tool

A Python utility for deploying websites to Cloudflare Pages using the Cloudflare API.

## Features

- Deploy static websites to Cloudflare Pages
- Authenticate with Cloudflare API tokens
- Upload files with proper content types
- Monitor deployment status
- Command-line interface for easy integration

## Prerequisites

- Python 3.7 or higher
- Cloudflare account with Pages enabled
- Cloudflare API token with Pages permissions
- Cloudflare Account ID

## Installation

1. Clone this repository or download the files
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

You'll need the following information to use this tool:

1. **Cloudflare API Token**: Create a token with Pages permissions in your Cloudflare dashboard
2. **Cloudflare Account ID**: Found in the URL when you're logged into the Cloudflare dashboard
3. **Pages Project Name**: The name of your Cloudflare Pages project

## Usage

```bash
# Deploy to an existing project
python cloudflare_pages_deploy.py --token YOUR_API_TOKEN --account YOUR_ACCOUNT_ID --project YOUR_PROJECT_NAME --directory ./path/to/site

# Create a new project if it doesn't exist
python cloudflare_pages_deploy.py --token YOUR_API_TOKEN --account YOUR_ACCOUNT_ID --project YOUR_PROJECT_NAME --directory ./path/to/site --create-new

# Create a unique project with timestamp for each deployment
python cloudflare_pages_deploy.py --token YOUR_API_TOKEN --account YOUR_ACCOUNT_ID --project YOUR_PROJECT_NAME --directory ./path/to/site --unique
```

### Command-line Options

- `--token`, `-t`: Cloudflare API token (required)
- `--account`, `-a`: Cloudflare account ID (required)
- `--project`, `-p`: Pages project name (required)
- `--directory`, `-d`: Directory containing files to deploy (required)
- `--timeout`: Maximum time to wait for deployment completion in seconds (default: 300)

## Example

```bash
python cloudflare_pages_deploy.py --token 1234567890abcdef --account 1a2b3c4d5e6f7g8h9i0j --project my-website --directory ./dist
```

## Error Handling

The tool provides detailed error messages for common issues:

- Invalid API token or account ID
- Project not found
- Upload failures
- Deployment timeouts or failures

## License

MIT