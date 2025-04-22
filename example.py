#!/usr/bin/env python3
"""
Example script demonstrating how to use the CloudflarePagesDeployer class programmatically.
"""

import os
import time
from datetime import datetime
from lib import CloudflarePagesDeployer, CloudflareAPIError

# Replace these with your actual values
API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "your_api_token_here")
ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "your_account_id_here")
PROJECT_NAME = os.environ.get("CLOUDFLARE_PROJECT_NAME", "your_project_name_here")
DIRECTORY_PATH = "./dist"  # Path to your build directory

def deploy_to_cloudflare_pages(create_new_project=True):
    """Example function to deploy a site to Cloudflare Pages.
    
    Args:
        create_new_project: If True, create a new project for this deployment
    """
    try:
        # Initialize the deployer
        deployer = CloudflarePagesDeployer(API_TOKEN, ACCOUNT_ID)
        
        # List available projects
        print("Available projects:")
        projects = deployer.list_projects()
        for project in projects:
            print(f"- {project['name']}")
        
        # Generate a unique project name if creating a new project
        if create_new_project:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            unique_project_name = f"{PROJECT_NAME}-{timestamp}"
            print(f"\nCreating new project: {unique_project_name}")
        else:
            unique_project_name = PROJECT_NAME
            print(f"\nUsing existing project: {unique_project_name}")
        
        # Create a new deployment
        print(f"Creating deployment for {unique_project_name}...")
        deployment = deployer.create_deployment(
            unique_project_name, 
            create_if_not_exists=create_new_project
        )
        deployment_id = deployment.get("id")
        
        # Upload files
        print(f"Uploading files from {DIRECTORY_PATH}...")
        deployer.upload_files(deployment, DIRECTORY_PATH)
        
        # Wait for deployment to complete
        print("Waiting for deployment to complete...")
        final_status = deployer.wait_for_deployment(unique_project_name, deployment_id)
        
        # Print deployment URL
        url = final_status.get("url")
        if url:
            print(f"\nDeployment successful! Your site is live at: {url}")
        else:
            print("\nDeployment successful!")
            
    except CloudflareAPIError as e:
        print(f"Cloudflare API Error: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Set to True to create a new project for each deployment
    # Set to False to use the existing project specified in PROJECT_NAME
    deploy_to_cloudflare_pages(create_new_project=True)