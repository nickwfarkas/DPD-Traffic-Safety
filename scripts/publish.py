import tableauserverclient as TSC
import os
import argparse
from typing import Optional

# Tableau Cloud credentials
SITE_NAME = ''  # Your Tableau Cloud site name
API_KEY = ''    # Your Personal Access Token Name
API_SECRET = '' # Your Personal Access Token Secret

def publish_workbook(
    twb_path: str,
    project_name: str,
    site_name: Optional[str] = None,
    overwrite: bool = True
) -> None:
    """
    Publish a Tableau workbook to Tableau Cloud.
    
    Args:
        twb_path (str): Path to the .twb file
        project_name (str): Name of the project to publish to
        site_name (str, optional): Tableau Cloud site name. Defaults to SITE_NAME.
        overwrite (bool, optional): Whether to overwrite existing workbook. Defaults to True.
    """
    if not os.path.exists(twb_path):
        raise FileNotFoundError(f"Workbook file not found: {twb_path}")

    # Use provided site name or default
    site_name = site_name or SITE_NAME

    # Create authentication object
    tableau_auth = TSC.PersonalAccessTokenAuth(
        token_name=API_KEY,
        personal_access_token=API_SECRET,
        site_id=site_name
    )

    # Create server object
    server = TSC.Server('https://online.tableau.com')

    # Sign in to server
    with server.auth.sign_in(tableau_auth):
        # Get project
        all_projects, pagination_item = server.projects.get()
        project = next((p for p in all_projects if p.name == project_name), None)
        
        if not project:
            raise ValueError(f"Project '{project_name}' not found")

        # Create workbook item
        workbook = TSC.WorkbookItem(project.id)

        # Publish workbook
        workbook = server.workbooks.publish(
            workbook,
            twb_path,
            mode=TSC.Server.PublishMode.Overwrite if overwrite else TSC.Server.PublishMode.CreateNew
        )
        
        print(f"Successfully published workbook to project: {project_name}")

def main():
    parser = argparse.ArgumentParser(description='Publish Tableau workbook to Tableau Cloud')
    parser.add_argument('twb_path', help='Path to the .twb file')
    parser.add_argument('project_name', help='Name of the project to publish to')
    parser.add_argument('--site-name', help='Tableau Cloud site name (optional)')
    parser.add_argument('--no-overwrite', action='store_true', help='Do not overwrite existing workbook')
    
    args = parser.parse_args()
    
    try:
        publish_workbook(
            args.twb_path,
            args.project_name,
            site_name=args.site_name,
            overwrite=not args.no_overwrite
        )
    except Exception as e:
        print(f"Error publishing workbook: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
