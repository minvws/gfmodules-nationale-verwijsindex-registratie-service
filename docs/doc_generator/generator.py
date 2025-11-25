"""
Original author : Aman Ulla
Description: This is a Project to Generate Markdown API Documentation for FastAPI OpenAPI specs

MIT License

Copyright (c) 2024 Aman Ulla 

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from typing import Any, Dict


def generate_api_docs(openapi: Dict[str, Any]) -> str:
    """
    Generates API documentation from an OpenAPI JSON string.

    Args:
        openapi (Dict[str, Any]): The OpenAPI specification as a dictionary.

    Returns:
        str: The generated markdown documentation.
    """
    markdown_content = ""
    
    paths = openapi.get('paths', {})
    components = openapi.get('components', {})

    for path, methods in paths.items():
        for method, details in methods.items():
            markdown_content += f"\n### {details.get('summary', '')}\n"
            markdown_content += f"\n\n{details.get('description', '')}\n\n"
            markdown_content += "| Method | URL |\n|--------|-----|\n"
            markdown_content += f"| {method.upper()} | {path} |\n"
            markdown_content += "\n#### Parameters\n"
            markdown_content += "| Name | In | Description | Required |\n|------|----|-------------|----------|\n"
            
            for param in details.get('parameters', []):
                description = param['schema'].get('description', '')
                required = "Required" if param.get('required', False) else "Optional"
                markdown_content += f"| {param.get('name')} | {param.get('in')} | {description} | {required} |\n"
            
            if 'requestBody' in details:
                markdown_content += "\n##### Request Body\n"
                request_body = details['requestBody']
                content_type, schema_info = next(iter(request_body.get('content').items()))
                markdown_content += "| Field | Type | Description | Required |\n|-------|------|-------------|----------|\n"
                for prop_name, prop_details in schema_info.get('schema', {}).get('properties', {}).items():
                    required = "Required" if prop_name in schema_info.get('schema', {}).get('required', []) else "Optional"
                    markdown_content += f"| {prop_name} | {prop_details.get('type', 'N/A')} | {prop_details.get('description', '')} | {required} |\n"
            
            responses = details.get('responses', {})
            for status_code, response in responses.items():
                markdown_content += f"\n##### Response ({status_code})\n"
                markdown_content += "| Field | Type | Description |\n|-------|------|-------------|\n"
                for content_type, content_info in response.get('content', {}).items():
                    for prop_name, prop_details in content_info.get('schema', {}).get('properties', {}).items():
                        markdown_content += f"| {prop_name} | {prop_details.get('type', 'N/A')} | {prop_details.get('description', '')} |\n"
            
            markdown_content += '\n---\n'
    return markdown_content
