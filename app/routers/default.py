import json
import logging
from pathlib import Path

from fastapi import APIRouter, Response

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


@router.get("/", summary="API Home", description="Displays the API logo and version information.")
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


@router.get("/version.json", summary="Get Version Info", description="Retrieve the API version information.")
def version_json() -> Response:
    try:
        with open(Path(__file__).parent.parent.parent / "version.json", "r") as file:
            content = file.read()
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.info("Version info could not be loaded: %s" % e)
        return Response(status_code=404)

    return Response(content)
