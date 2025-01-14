####
# This script demonstrates how to export a view using the Tableau
# Server Client.
#
# To run the script, you must have installed Python 3.7 or later.
####

import argparse
import logging

import tableauserverclient as TSC


def main():
    parser = argparse.ArgumentParser(description="Export a view as an image, PDF, or CSV")
    # Common options; please keep those in sync across all samples
    parser.add_argument("--server", "-s", help="server address", default="https://prod-useast-a.online.tableau.com")
    parser.add_argument("--site", "-S", help="site name", default="roofconnect")
    parser.add_argument("--token-name", "-p", help="name of the personal access token used to sign into the server", default="StephenAdminPAT")
    parser.add_argument("--token-value", "-v", help="value of the personal access token used to sign into the server", default="rICUXGTWTNSpIiOZ3LS57A==:9UXmB6wQbvpVUIsPlYmt1VnxEv5XI1Tb")
        # Set PNG as default type without requiring argument
    parser.add_argument("--type", default=("populate_views", "ImageRequestOptions", "image", "png"))
    #parser.add_argument("--png", dest="type", action="store_const", const=("populate_image", "ImageRequestOptions", "image", "png"), default="png")
    parser.add_argument(
        "--logging-level",
        "-l",
        choices=["debug", "info", "error"],
        default="error",
        help="desired logging level (set to error by default)",
    )
    # Options specific to this sample
    group = parser.add_mutually_exclusive_group(required=False)
    #group.add_argument(
    #    "--pdf", dest="type", action="store_const", const=("populate_pdf", "PDFRequestOptions", "pdf", "pdf")
    #)
    group.add_argument(
        "--png", dest="type", action="store_const", const=("populate_image", "ImageRequestOptions", "image", "png"), default="png"
    )
    #group.add_argument(
    #    "--csv", dest="type", action="store_const", const=("populate_csv", "CSVRequestOptions", "csv", "csv")
    #)
    # other options shown in explore_workbooks: workbook.download, workbook.preview_image
    parser.add_argument(
        "--language", help="Text such as 'Average' will appear in this language. Use values like fr, de, es, en", default="en")
    parser.add_argument("--workbook", action="store_true", default="Company Weekly Game r2")
    parser.add_argument("--custom_view", action="store_true", default="WeeklyDayOff_1")

    parser.add_argument("--file", "-f", help="filename to store the exported data", default="Weekly Game Export")
    #parser.add_argument("--filter", "-vf", metavar="COLUMN:VALUE", help="View filter to apply to the view")
    parser.add_argument("--resource_id", help="LUID for the view or workbook", default="c7879dd9-daba-4aa3-aeeb-35ba8c33f4ca")

    args = parser.parse_args()

    # Set logging level based on user input, or error by default
    logging_level = getattr(logging, args.logging_level.upper())
    logging.basicConfig(level=logging_level)

    tableau_auth = TSC.PersonalAccessTokenAuth(args.token_name, args.token_value, site_id=args.site)
    server = TSC.Server(args.server, use_server_version=True, http_options={"verify": False})
    with server.auth.sign_in(tableau_auth):
        print("Connected")
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
    
    # Unpack export type information
    (populate_func_name, option_factory_name, member_name, extension) = args.type
    
    # Get the correct populate method based on item type
    if args.workbook:
        populate = getattr(server.workbooks, populate_func_name)
    elif args.custom_view:
        populate = getattr(server.custom_views, populate_func_name)
    else:
        populate = getattr(server.views, populate_func_name)

    # Create export options
    option_factory = getattr(TSC, option_factory_name)
    options = option_factory()
    
    # Export the item
    file_path = f"{args.file}.{extension}"
    exported_content = populate(item, options)
    
    # Save to file
    with open(file_path, 'wb') as f:
        f.write(exported_content)
    
    print(f"Export saved to: {file_path}")

if __name__ == "__main__":
    main()

#TODO resolve error:
#    f.write(exported_content)
#    ~~~~~~~^^^^^^^^^^^^^^^^^^
#TypeError: a bytes-like object is required, not 'NoneType'