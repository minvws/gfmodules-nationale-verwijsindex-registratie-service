import json
import logging
from pathlib import Path

from fastapi import APIRouter, Response, status

logger = logging.getLogger(__name__)
router = APIRouter()

# https://www.patorjk.com/software/taag/#p=display&f=Doom&t=Skeleton
LOGO = r"""

 _   _ ______ _____     ______           _     _             _   _
| \ | || ___ \_   _|    | ___ \         (_)   | |           | | (_)
|  \| || |_/ / | |______| |_/ /___  __ _ _ ___| |_ _ __ __ _| |_ _  ___  _ __
| . ` ||    /  | |______|    // _ \/ _` | / __| __| '__/ _` | __| |/ _ \| '_ \
| |\  || |\ \ _| |_     | |\ \  __/ (_| | \__ \ |_| | | (_| | |_| | (_) | | | |
\_| \_/\_| \_|\___/     \_| \_\___|\__, |_|___/\__|_|  \__,_|\__|_|\___/|_| |_|
                                    __/ |
                                   |___/
"""


@router.get(
    "/",
    summary="API Home",
    description="""Display the NVI Registration Service welcome page with ASCII logo and version information.
    
    This endpoint serves as the root entry point for the API, providing:
    - Service identification via ASCII art logo
    - Current service version
    - Git commit reference for deployment tracking
    
    Returns plain text for easy terminal/browser viewing.
    """,
    response_class=Response,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "API home page with logo and version info",
            "content": {
                "text/plain": {
                    "example": """NVI-Registration\n\nVersion: 1.0.0\nCommit: abc123def456"""
                }
            }
        }
    },
    tags=["Info"]
)
def index() -> Response:
    content = LOGO

    try:
        with open(Path(__file__).parent.parent.parent / "version.json", "r") as file:
            data = json.load(file)
            content += "\nVersion: %s\nCommit: %s" % (data["version"], data["git_ref"])
    except (FileNotFoundError, json.JSONDecodeError) as e:
        content += "\nNo version information found"
        logger.info("Version info could not be loaded: %s" % e)

    return Response(content)


@router.get(
    "/version.json",
    summary="Get Version Info",
    description="""Retrieve detailed version and build information in JSON format.
    
    Returns structured version information including:
    - Semantic version number
    - Git commit hash/reference
    - Build timestamp (if available)
    - Other build metadata
    
    This endpoint is useful for:
    - Automated deployment verification
    - Version tracking in monitoring systems
    - Programmatic version checks
    """,
    response_class=Response,
    responses={
        200: {
            "description": "Version information retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "version": "1.0.0",
                        "git_ref": "abc123def456",
                        "build_date": "2025-11-25T10:00:00Z"
                    }
                }
            }
        },
        404: {
            "description": "Version information file not found"
        }
    },
    tags=["Info"]
)
def version_json() -> Response:
    try:
        with open(Path(__file__).parent.parent.parent / "version.json", "r") as file:
            content = file.read()
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.info("Version info could not be loaded: %s" % e)
        return Response(status_code=404, )

    return Response(content)
