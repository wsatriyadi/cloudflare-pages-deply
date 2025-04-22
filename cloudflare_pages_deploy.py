#!/usr/bin/env python3
"""
Cloudflare Pages Deployment Tool

A Python script to deploy websites to Cloudflare Pages using the Cloudflare API.
"""

import sys
import argparse
from datetime import datetime

# Import from the lib directory
from lib.cloudflare import CloudflarePagesDeployer, CloudflareAPIError


def main():
    """Main function to handle CLI arguments and execute deployment."""
    parser = argparse.ArgumentParser(description="Deploy to Cloudflare Pages")
    parser.add_argument("--token", "-t", required=True, help="Cloudflare API token")
    parser.add_argument("--account", "-a", required=True, help="Cloudflare account ID")
    parser.add_argument("--project", "-p", required=True, help="Pages project name")
    parser.add_argument("--directory", "-d", required=True, help="Directory to deploy")
    parser.add_argument("--timeout", type=int, default=300, help="Deployment timeout in seconds")
    parser.add_argument("--create-new", "-c", action="store_true", help="Create a new project if it doesn't exist")
    parser.add_argument("--unique", "-u", action="store_true", help="Create a unique project name with timestamp")
    
    args = parser.parse_args()
    
    try:
        # Initialize deployer
        deployer = CloudflarePagesDeployer(args.token, args.account)
        
        # Generate a unique project name if requested
        project_name = args.project
        if args.unique:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            project_name = f"{args.project}-{timestamp}"
            print(f"Using unique project name: {project_name}")
        
        # Verify project exists if not creating a new one
        if not args.create_new and not args.unique:
            try:
                project = deployer.get_project(project_name)
                print(f"Found project: {project['name']}")
            except CloudflareAPIError:
                print(f"Project '{project_name}' not found. Available projects:")
                projects = deployer.list_projects()
                for project in projects:
                    print(f"- {project['name']}")
                return 1
        
        # Create deployment
        print("Creating deployment...")
        deployment = deployer.create_deployment(
            project_name, 
            create_if_not_exists=(args.create_new or args.unique)
        )
        deployment_id = deployment.get("id")
        if not deployment_id:
            print("Failed to create deployment: No deployment ID returned")
            return 1
        
        print(f"Deployment created with ID: {deployment_id}")
        
        # Upload files
        print(f"Uploading files from {args.directory}...")
        deployer.upload_files(deployment, args.directory)
        
        # Wait for deployment to complete
        print("Waiting for deployment to complete...")
        final_status = deployer.wait_for_deployment(
            project_name, deployment_id, timeout=args.timeout
        )
        
        # Print deployment URL
        url = final_status.get("url")
        if url:
            print(f"\nDeployment successful! Your site is live at: {url}")
        else:
            print("\nDeployment successful!")
        
        return 0
    
    except CloudflareAPIError as e:
        print(f"Cloudflare API Error: {str(e)}")
        return 1
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())