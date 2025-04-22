#!/usr/bin/env python3
"""
Cloudflare Pages Deployment Tool

A Python module to deploy websites to Cloudflare Pages using the Cloudflare API.
"""

import os
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime


class CloudflareAPIError(Exception):
    """Exception raised for Cloudflare API errors."""
    pass


class CloudflarePagesDeployer:
    """Class to handle deployments to Cloudflare Pages."""

    def __init__(self, api_token: str, account_id: str):
        """
        Initialize the deployer with authentication details.
        
        Args:
            api_token: Cloudflare API token with Pages permissions
            account_id: Cloudflare account ID
        """
        self.api_token = api_token
        self.account_id = account_id
        self.base_url = "https://api.cloudflare.com/client/v4"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                      files: Optional[Dict] = None) -> Dict:
        """
        Make a request to the Cloudflare API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint to call
            data: Optional data to send with the request
            files: Optional files to upload
            
        Returns:
            Response data as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        
        # For file uploads, we don't want to send JSON data
        headers = self.headers.copy()
        if files:
            # Remove Content-Type for multipart/form-data
            headers.pop("Content-Type", None)
        
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data if data and not files else None,
            data=data if files else None,
            files=files
        )
        
        try:
            result = response.json()
        except json.JSONDecodeError:
            raise CloudflareAPIError(f"Invalid JSON response: {response.text}")
        
        if not result.get("success", False):
            errors = result.get("errors", [])
            error_msg = "; ".join([error.get("message", "Unknown error") for error in errors])
            raise CloudflareAPIError(f"API request failed: {error_msg}")
        
        return result
    
    def list_projects(self) -> List[Dict]:
        """
        List all Cloudflare Pages projects in the account.
        
        Returns:
            List of projects
        """
        result = self._make_request(
            "GET", 
            f"/accounts/{self.account_id}/pages/projects"
        )
        return result.get("result", [])
    
    def get_project(self, project_name: str) -> Dict:
        """
        Get details about a specific Pages project.
        
        Args:
            project_name: Name of the Pages project
            
        Returns:
            Project details
        """
        result = self._make_request(
            "GET", 
            f"/accounts/{self.account_id}/pages/projects/{project_name}"
        )
        return result.get("result", {})
    
    def create_project(self, project_name: str, production_branch: str = "main") -> Dict:
        """
        Create a new Cloudflare Pages project.
        
        Args:
            project_name: Name of the Pages project to create
            production_branch: The git branch to use for production deployments (default: "main")
            
        Returns:
            Project details of the newly created project
        """
        data = {
            "name": project_name,
            "production_branch": production_branch
        }
        
        result = self._make_request(
            "POST", 
            f"/accounts/{self.account_id}/pages/projects",
            data=data
        )
        return result.get("result", {})
    
    def create_deployment(self, project_name: str, create_if_not_exists: bool = False, production_branch: str = "main") -> Dict:
        """
        Create a new deployment for a Pages project.
        
        Args:
            project_name: Name of the Pages project
            create_if_not_exists: If True, create the project if it doesn't exist
            production_branch: The git branch to use for production deployments if creating a new project
            
        Returns:
            Deployment details including upload URL
        """
        # Check if project exists and create it if needed
        if create_if_not_exists:
            try:
                self.get_project(project_name)
                print(f"Using existing project: {project_name}")
            except CloudflareAPIError:
                print(f"Project '{project_name}' not found. Creating new project...")
                self.create_project(project_name, production_branch)
                print(f"Project '{project_name}' created successfully.")
        
        result = self._make_request(
            "POST", 
            f"/accounts/{self.account_id}/pages/projects/{project_name}/deployments"
        )
        return result.get("result", {})
    
    def upload_files(self, deployment: Dict, directory_path: str) -> bool:
        """
        Upload files for a deployment.
        
        Args:
            deployment: Deployment details from create_deployment
            directory_path: Path to the directory containing files to upload
            
        Returns:
            True if successful
        """
        # Get upload details from deployment
        upload_url = deployment.get("upload_url")
        if not upload_url:
            raise CloudflareAPIError("No upload URL provided in deployment")
        
        # Prepare files for upload
        files_to_upload = self._prepare_files(directory_path)
        print(f"Preparing to upload {len(files_to_upload)} files...")
        
        # Upload files in batches to avoid request size limits
        batch_size = 10
        for i in range(0, len(files_to_upload), batch_size):
            batch = files_to_upload[i:i+batch_size]
            files_dict = {}
            manifest = {}
            
            for file_path, file_info in batch:
                rel_path = file_info["path"]
                files_dict[rel_path] = (rel_path, open(file_path, "rb"), file_info["content_type"])
                manifest[rel_path] = {"size": file_info["size"], "type": file_info["content_type"]}
            
            # Add manifest to the files
            manifest_json = json.dumps(manifest)
            files_dict["manifest.json"] = ("manifest.json", manifest_json, "application/json")
            
            try:
                # Upload the batch
                response = requests.post(upload_url, files=files_dict)
                if response.status_code != 200:
                    raise CloudflareAPIError(f"Upload failed: {response.text}")
                
                print(f"Uploaded batch {i//batch_size + 1}/{(len(files_to_upload) + batch_size - 1)//batch_size}")
                
                # Close all file handles
                for _, file_tuple, _ in files_dict.values():
                    if hasattr(file_tuple, "close"):
                        file_tuple.close()
            except Exception as e:
                # Close all file handles on error
                for _, file_tuple, _ in files_dict.values():
                    if hasattr(file_tuple, "close"):
                        file_tuple.close()
                raise e
        
        return True
    
    def _prepare_files(self, directory_path: str) -> List[Tuple[str, Dict]]:
        """
        Prepare files for upload by gathering metadata.
        
        Args:
            directory_path: Path to the directory containing files to upload
            
        Returns:
            List of tuples (file_path, file_info)
        """
        files_to_upload = []
        directory = Path(directory_path)
        
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Directory not found: {directory_path}")
        
        # Common content types
        content_types = {
            ".html": "text/html",
            ".css": "text/css",
            ".js": "application/javascript",
            ".json": "application/json",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon",
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".pdf": "application/pdf",
            ".woff": "font/woff",
            ".woff2": "font/woff2",
            ".ttf": "font/ttf",
            ".eot": "application/vnd.ms-fontobject",
            ".otf": "font/otf",
            ".xml": "application/xml",
        }
        
        # Default content type
        default_content_type = "application/octet-stream"
        
        for file_path in directory.glob("**/*"):
            if file_path.is_file():
                # Get relative path for upload
                rel_path = str(file_path.relative_to(directory)).replace("\\", "/")
                
                # Determine content type based on file extension
                content_type = content_types.get(file_path.suffix.lower(), default_content_type)
                
                # Get file size
                size = file_path.stat().st_size
                
                files_to_upload.append((str(file_path), {
                    "path": rel_path,
                    "size": size,
                    "content_type": content_type
                }))
        
        return files_to_upload
    
    def get_deployment_status(self, project_name: str, deployment_id: str) -> Dict:
        """
        Get the status of a deployment.
        
        Args:
            project_name: Name of the Pages project
            deployment_id: ID of the deployment
            
        Returns:
            Deployment status details
        """
        result = self._make_request(
            "GET", 
            f"/accounts/{self.account_id}/pages/projects/{project_name}/deployments/{deployment_id}"
        )
        return result.get("result", {})
    
    def wait_for_deployment(self, project_name: str, deployment_id: str, 
                           timeout: int = 300, interval: int = 5) -> Dict:
        """
        Wait for a deployment to complete.
        
        Args:
            project_name: Name of the Pages project
            deployment_id: ID of the deployment
            timeout: Maximum time to wait in seconds
            interval: Time between status checks in seconds
            
        Returns:
            Final deployment status
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.get_deployment_status(project_name, deployment_id)
            stage = status.get("stage", "")
            
            print(f"Deployment status: {stage}")
            
            if stage == "success":
                return status
            elif stage in ["failed", "canceled"]:
                raise CloudflareAPIError(f"Deployment {stage}: {status.get('error_message', 'Unknown error')}")
            
            time.sleep(interval)
        
        raise CloudflareAPIError(f"Deployment timed out after {timeout} seconds")