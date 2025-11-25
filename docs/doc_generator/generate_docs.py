from typing import Any, Dict
from unittest.mock import patch
from docs.doc_generator.generator import generate_api_docs
from app.application import create_fastapi_app
from app.config import set_config
from app.models.ura_number import UraNumber
from tests.test_config import get_test_config

MARKDOWN_OUTPUT_PATH = "./docs/interface-definitions/api-definitions.md"


def get_api_client() -> Dict[str, Any]:
    cfg = get_test_config()
    set_config(cfg)

    with patch("app.services.ura.UraNumberService.get_ura_number") as mocked_ura:
        mocked_ura.return_value = UraNumber("12345678")

        app = create_fastapi_app()
        return app.openapi()


def generate_markdown(
    openapi_data: Dict[str, Any]
) -> None:
    result = generate_api_docs(openapi_data)
    with open(MARKDOWN_OUTPUT_PATH, "w") as md_file:
        md_file.write(result)
    print(f"Markdown docs generated at: {MARKDOWN_OUTPUT_PATH}")


def main() -> None:
    openapi_data = get_api_client()
    generate_markdown(openapi_data)


if __name__ == "__main__":
    main()
