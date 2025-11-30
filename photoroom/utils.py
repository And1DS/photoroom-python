"""PhotoRoom API Utility Functions.

This module provides helper functions for file I/O, parameter validation,
and response header extraction.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from httpx import Response


def load_image_file(
    image_path: Union[str, Path],
    validate: bool = False,
    auto_resize: bool = False,
    auto_convert: bool = False,
) -> bytes:
    """Load image file from disk with optional validation.

    Args:
        image_path: Path to image file
        validate: Whether to validate the image before returning
        auto_resize: Automatically resize if image exceeds size/dimension limits
        auto_convert: Automatically convert unsupported formats to WebP

    Returns:
        Binary image data (potentially validated/converted/resized)

    Raises:
        FileNotFoundError: If image file doesn't exist
        IOError: If file cannot be read
        ImageValidationError: If validation fails and auto-fix is disabled
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    if not path.is_file():
        raise IOError(f"Path is not a file: {image_path}")

    image_data = path.read_bytes()

    # Validate and prepare image if requested
    if validate:
        from .validation import validate_and_prepare_image
        image_data = validate_and_prepare_image(
            image_data,
            file_path=image_path,
            auto_resize=auto_resize,
            auto_convert=auto_convert,
            validate=True,
        )

    return image_data


def save_image_file(image_data: bytes, output_path: Union[str, Path]) -> None:
    """Save image data to disk.

    Args:
        image_data: Binary image data
        output_path: Path where image should be saved

    Raises:
        IOError: If file cannot be written
    """
    path = Path(output_path)

    # Create parent directories if they don't exist
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_bytes(image_data)


def extract_response_metadata(response: Response) -> Dict[str, Any]:
    """Extract metadata from HTTP response headers.

    Captures PhotoRoom-specific headers like pr-ai-background-seed,
    pr-texts-detected, pr-edit-further-url, etc.

    Args:
        response: HTTPX Response object

    Returns:
        Dictionary containing relevant response headers
    """
    metadata: Dict[str, Any] = {}

    # List of PhotoRoom-specific headers to capture
    pr_headers = [
        "pr-ai-background-seed",
        "pr-texts-detected",
        "pr-unsupported-attributes",
        "pr-edit-further-url",
    ]

    for header in pr_headers:
        value = response.headers.get(header)
        if value is not None:
            metadata[header] = value

    # Also capture content-type
    content_type = response.headers.get("content-type")
    if content_type:
        metadata["content-type"] = content_type

    return metadata


def get_api_key(api_key: Optional[str] = None) -> str:
    """Get API key from parameter or environment variable.

    Args:
        api_key: Explicit API key (optional)

    Returns:
        API key string

    Raises:
        ValueError: If no API key is provided or found in environment
    """
    if api_key:
        return api_key

    # Try to load from environment
    env_key = os.environ.get("PHOTOROOM_API_KEY")
    if env_key:
        return env_key

    # Try to load from .env file if python-dotenv is available
    try:
        from dotenv import load_dotenv

        load_dotenv()
        env_key = os.environ.get("PHOTOROOM_API_KEY")
        if env_key:
            return env_key
    except ImportError:
        pass

    raise ValueError(
        "No API key provided. Please provide api_key parameter or set "
        "PHOTOROOM_API_KEY environment variable."
    )


def build_multipart_data(
    image_file: Optional[bytes] = None,
    image_file_name: str = "image.jpg",
    **params: Any,
) -> Dict[str, Any]:
    """Build multipart form data for API request.

    Args:
        image_file: Binary image data (optional)
        image_file_name: Filename to use for image upload
        **params: Additional form parameters

    Returns:
        Dictionary suitable for httpx multipart/form-data request
    """
    data: Dict[str, Any] = {}

    # Add image file if provided
    if image_file is not None:
        data["imageFile"] = (image_file_name, image_file, "image/jpeg")

    # Add other parameters, filtering out None values
    for key, value in params.items():
        if value is not None:
            # Convert nested parameters (e.g., background_color -> background.color)
            # This is already handled by the endpoint methods
            data[key] = value

    return data


def normalize_param_name(python_name: str) -> str:
    """Convert Python parameter name to API parameter name.

    Converts snake_case to dot notation where applicable.
    Example: background_color -> background.color

    Args:
        python_name: Python-style parameter name (snake_case)

    Returns:
        API-style parameter name (dot notation)
    """
    # Map of known parameter name conversions
    conversions = {
        # Background parameters
        "background_blur_mode": "background.blur.mode",
        "background_blur_radius": "background.blur.radius",
        "background_color": "background.color",
        "background_expand_prompt": "background.expandPrompt",
        "background_guidance_image_file": "background.guidance.imageFile",
        "background_guidance_image_url": "background.guidance.imageUrl",
        "background_guidance_scale": "background.guidance.scale",
        "background_image_url": "background.imageUrl",
        "background_image_file": "background.imageFile",
        "background_negative_prompt": "background.negativePrompt",
        "background_prompt": "background.prompt",
        "background_scaling": "background.scaling",
        "background_seed": "background.seed",
        # Beautify parameters
        "beautify_mode": "beautify.mode",
        "beautify_seed": "beautify.seed",
        # Expand parameters
        "expand_mode": "expand.mode",
        "expand_seed": "expand.seed",
        # Export parameters
        "export_dpi": "export.dpi",
        "export_format": "export.format",
        # Image from prompt parameters
        "image_from_prompt_prompt": "imageFromPrompt.prompt",
        "image_from_prompt_seed": "imageFromPrompt.seed",
        "image_from_prompt_size": "imageFromPrompt.size",
        # Lighting parameters
        "lighting_mode": "lighting.mode",
        # Segmentation parameters
        "segmentation_mode": "segmentation.mode",
        "segmentation_negative_prompt": "segmentation.negativePrompt",
        "segmentation_prompt": "segmentation.prompt",
        # Shadow parameters
        "shadow_mode": "shadow.mode",
        # Text removal parameters
        "text_removal_mode": "textRemoval.mode",
        # Uncrop parameters
        "uncrop_mode": "uncrop.mode",
        "uncrop_seed": "uncrop.seed",
        # Upscale parameters
        "upscale_mode": "upscale.mode",
        # Simple conversions
        "image_url": "imageUrl",
        "image_file": "imageFile",
        "output_size": "outputSize",
        "remove_background": "removeBackground",
        "horizontal_alignment": "horizontalAlignment",
        "vertical_alignment": "verticalAlignment",
        "reference_box": "referenceBox",
        "template_id": "templateId",
        "preserve_metadata": "preserveMetadata",
        "keep_existing_alpha_channel": "keepExistingAlphaChannel",
        "ignore_padding_and_snap_on_cropped_sides": "ignorePaddingAndSnapOnCroppedSides",
        "margin_top": "marginTop",
        "margin_bottom": "marginBottom",
        "margin_left": "marginLeft",
        "margin_right": "marginRight",
        "padding_top": "paddingTop",
        "padding_bottom": "paddingBottom",
        "padding_left": "paddingLeft",
        "padding_right": "paddingRight",
        "max_width": "maxWidth",
        "max_height": "maxHeight",
    }

    return conversions.get(python_name, python_name)
