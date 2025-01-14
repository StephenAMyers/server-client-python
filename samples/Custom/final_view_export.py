import argparse
import logging
import tableauserverclient as TSC

def main():
    parser = argparse.ArgumentParser(description="Export a view as an image")
    
    # Common options
    parser.add_argument("--server", "-s", help="server address", 
                       default="https://prod-useast-a.online.tableau.com")
    parser.add_argument("--site", "-S", help="site name", 
                       default="roofconnect")
    parser.add_argument("--token-name", "-p", help="name of the personal access token", 
                       default="StephenAdminPAT")
    parser.add_argument("--token-value", "-v", help="value of the personal access token", 
                       default="rICUXGTWTNSpIiOZ3LS57A==:9UXmB6wQbvpVUIsPlYmt1VnxEv5XI1Tb")
    
    # Export options
    parser.add_argument("--type", 
                       default=("populate_image", "ImageRequestOptions", "image", "png"))
    parser.add_argument("--logging-level", "-l",
                       choices=["debug", "info", "error"],
                       default="error",
                       help="desired logging level")
    
    # Resource options
    parser.add_argument("--language", help="Language code", 
                       default="en")
    parser.add_argument("--workbook", action="store_true", 
                       default="Company Weekly Game r2")
    parser.add_argument("--custom_view", action="store_true", 
                       default="WeeklyDayOff_1")
    parser.add_argument("--file", "-f", help="filename to store the exported data", 
                       default="Weekly Game Export")
    parser.add_argument("--resource_id", help="LUID for the view or workbook", 
                       default="c7879dd9-daba-4aa3-aeeb-35ba8c33f4ca")

    args = parser.parse_args()

    # Configure logging
    logging_level = getattr(logging, args.logging_level.upper())
    logging.basicConfig(level=logging_level)

    # Authenticate
    tableau_auth = TSC.PersonalAccessTokenAuth(args.token_name, args.token_value, site_id=args.site)
    server = TSC.Server(args.server, use_server_version=True, http_options={"verify": False})

    with server.auth.sign_in(tableau_auth):
        print("Connected")
        
        # Get the resource
        if args.workbook:
            item = server.workbooks.get_by_id(args.resource_id)
        elif args.custom_view:
            item = server.custom_views.get_by_id(args.resource_id)
        else:
            item = server.views.get_by_id(args.resource_id)

        if not item:
            print(f"No item found for id {args.resource_id}")
            exit(1)

        print(f"Item found: {item.name}")

        try:
            # Create export options
            option_factory = getattr(TSC, "ImageRequestOptions")
            options = option_factory()
            
            # Export the item
            file_path = f"{args.file}.png"
            
            if args.workbook:
                exported_content = server.workbooks.populate_views(item)
            else:
                exported_content = server.views.populate_image(item)
            
            if exported_content:
                with open(file_path, 'wb') as f:
                    f.write(exported_content)
                print(f"Export saved to: {file_path}")
            else:
                print("Error: No content was exported")
                
        except Exception as e:
            print(f"Error during export: {str(e)}")
            exit(1)

if __name__ == "__main__":
    main()