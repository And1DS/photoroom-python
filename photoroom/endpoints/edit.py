"""PhotoRoom Image Editing Endpoint.

This module provides methods for editing images using the /v2/edit endpoint
(Plus plan). Supports 50+ parameters including background removal, AI backgrounds,
shadows, lighting, text removal, upscaling, and more.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Literal, Optional, Union

if TYPE_CHECKING:
    from ..client import PhotoRoomClient

from ..types import ImageResponse, PaddingMarginSpec
from ..utils import load_image_file, normalize_param_name


def edit_image(
    self: "PhotoRoomClient",
    image_file: Optional[Union[str, Path, bytes]] = None,
    image_url: Optional[str] = None,
    # Background parameters
    remove_background: Optional[bool] = True,
    background_color: Optional[str] = None,
    background_prompt: Optional[str] = None,
    background_image_url: Optional[str] = None,
    background_image_file: Optional[Union[str, Path, bytes]] = None,
    background_blur_mode: Optional[Literal["gaussian", "bokeh"]] = None,
    background_blur_radius: Optional[float] = None,
    background_expand_prompt: Optional[str] = None,
    background_guidance_image_url: Optional[str] = None,
    background_guidance_image_file: Optional[Union[str, Path, bytes]] = None,
    background_guidance_scale: Optional[float] = None,
    background_negative_prompt: Optional[str] = None,
    background_scaling: Optional[Literal["fit", "fill"]] = None,
    background_seed: Optional[int] = None,
    # Beautify parameters
    beautify_mode: Optional[Literal["ai.auto", "ai.food"]] = None,
    beautify_seed: Optional[int] = None,
    # Expand parameters
    expand_mode: Optional[Literal["ai.auto"]] = None,
    expand_seed: Optional[int] = None,
    # Export parameters
    export_format: Optional[Literal["png", "jpeg", "jpg", "webp"]] = "png",
    export_dpi: Optional[int] = None,
    # Positioning parameters
    horizontal_alignment: Optional[Literal["left", "center", "right"]] = None,
    vertical_alignment: Optional[Literal["top", "center", "bottom"]] = None,
    ignore_padding_and_snap_on_cropped_sides: Optional[bool] = None,
    # Image from prompt
    image_from_prompt_prompt: Optional[str] = None,
    image_from_prompt_seed: Optional[int] = None,
    image_from_prompt_size: Optional[
        Literal[
            "LANDSCAPE_16_9",
            "LANDSCAPE_4_3",
            "PORTRAIT_16_9",
            "PORTRAIT_4_3",
            "SQUARE_HD",
        ]
    ] = None,
    # Metadata
    keep_existing_alpha_channel: Optional[Literal["auto", "never"]] = None,
    preserve_metadata: Optional[Literal["never", "xmp", "exifSubset"]] = None,
    # Layers
    layers: Optional[Dict[str, Any]] = None,
    # Lighting
    lighting_mode: Optional[
        Literal["ai.auto", "ai.preserve-hue-and-saturation"]
    ] = None,
    # Size and padding parameters
    margin: Optional[PaddingMarginSpec] = None,
    margin_bottom: Optional[PaddingMarginSpec] = None,
    margin_left: Optional[PaddingMarginSpec] = None,
    margin_right: Optional[PaddingMarginSpec] = None,
    margin_top: Optional[PaddingMarginSpec] = None,
    max_height: Optional[int] = None,
    max_width: Optional[int] = None,
    output_size: Optional[str] = None,
    padding: Optional[PaddingMarginSpec] = None,
    padding_bottom: Optional[PaddingMarginSpec] = None,
    padding_left: Optional[PaddingMarginSpec] = None,
    padding_right: Optional[PaddingMarginSpec] = None,
    padding_top: Optional[PaddingMarginSpec] = None,
    # Reference and scaling
    reference_box: Optional[Literal["subjectBox", "originalImage"]] = None,
    scaling: Optional[Literal["fit", "fill"]] = None,
    # Segmentation
    segmentation_mode: Optional[
        Literal["keepSalientObject", "ignoreSalientObject"]
    ] = None,
    segmentation_negative_prompt: Optional[str] = None,
    segmentation_prompt: Optional[str] = None,
    # Shadow
    shadow_mode: Optional[Literal["ai.soft", "ai.hard", "ai.floating"]] = None,
    # Template
    template_id: Optional[str] = None,
    # Text removal
    text_removal_mode: Optional[Literal["ai.artificial", "ai.natural", "ai.all"]] = None,
    # Uncrop
    uncrop_mode: Optional[Literal["ai.auto"]] = None,
    uncrop_seed: Optional[int] = None,
    # Upscale
    upscale_mode: Optional[Literal["ai.fast", "ai.slow"]] = None,
    # Output
    output_file: Optional[Union[str, Path]] = None,
) -> ImageResponse:
    """Edit an image with AI-powered transformations.

    Uses the /v2/edit endpoint (Plus plan). Supports background removal,
    AI backgrounds, shadows, lighting adjustments, text removal, upscaling,
    and many other transformations.

    Args:
        image_file: Path to image file or binary image data (for POST)
        image_url: URL of image to process (for GET). Mutually exclusive with image_file.

        Background parameters:
            remove_background: Remove background (default: True)
            background_color: Background color (hex or name, e.g., "white", "FF0000")
            background_prompt: AI prompt for background generation
            background_image_url: URL of background image
            background_image_file: Background image file path or bytes
            background_blur_mode: Blur type - "gaussian" or "bokeh"
            background_blur_radius: Blur radius (0 to 0.05)
            background_expand_prompt: Prompt expansion mode
            background_guidance_image_url: URL of guidance image
            background_guidance_image_file: Guidance image file path or bytes
            background_guidance_scale: How closely to match guidance (0-1)
            background_negative_prompt: What to avoid in background
            background_scaling: "fit" or "fill"
            background_seed: Seed for reproducible backgrounds

        Beautify parameters:
            beautify_mode: "ai.auto" or "ai.food" - enhance product images
            beautify_seed: Seed for reproducible beautification

        Expand parameters:
            expand_mode: "ai.auto" - fill transparent pixels
            expand_seed: Seed for reproducible expansion

        Export parameters:
            export_format: Output format - "png", "jpeg", "jpg", or "webp"
            export_dpi: DPI for output (72-1200)

        Positioning:
            horizontal_alignment: "left", "center", or "right"
            vertical_alignment: "top", "center", or "bottom"
            ignore_padding_and_snap_on_cropped_sides: Snap cropped sides

        Image generation:
            image_from_prompt_prompt: Generate image from text
            image_from_prompt_seed: Seed for reproducible generation
            image_from_prompt_size: Size preset

        Metadata:
            keep_existing_alpha_channel: "auto" or "never"
            preserve_metadata: "never", "xmp", or "exifSubset"

        Layers:
            layers: Advanced layer composition (dict)

        Lighting:
            lighting_mode: "ai.auto" or "ai.preserve-hue-and-saturation"

        Size and padding:
            margin: General margin (0-0.49, "30%", or "100px")
            margin_bottom/left/right/top: Side-specific margins
            max_height: Maximum output height
            max_width: Maximum output width
            output_size: "auto", "WIDTHxHEIGHT", "originalImage", or "croppedSubject"
            padding: General padding (0-0.49, "30%", or "100px")
            padding_bottom/left/right/top: Side-specific padding

        Reference:
            reference_box: "subjectBox" or "originalImage"
            scaling: "fit" or "fill"

        Segmentation:
            segmentation_mode: "keepSalientObject" or "ignoreSalientObject"
            segmentation_negative_prompt: What to remove
            segmentation_prompt: What to keep

        Shadow:
            shadow_mode: "ai.soft", "ai.hard", or "ai.floating"

        Template:
            template_id: UUID of template to render

        Text removal:
            text_removal_mode: "ai.artificial", "ai.natural", or "ai.all"

        Uncrop:
            uncrop_mode: "ai.auto" - automatically uncrop subject
            uncrop_seed: Seed for reproducible uncropping

        Upscale:
            upscale_mode: "ai.fast" or "ai.slow" - 4x upscaling

        Output:
            output_file: Optional path to save result

    Returns:
        ImageResponse containing processed image and metadata

    Raises:
        ValueError: If neither image_file nor image_url provided
        FileNotFoundError: If image file path doesn't exist
        PhotoRoomBadRequest: If parameters are invalid (400)
        PhotoRoomPaymentError: If quota exceeded (402)
        PhotoRoomAuthError: If API key is invalid (403)

    Examples:
        >>> client = PhotoRoomClient()
        >>>
        >>> # Remove background with white color
        >>> result = client.edit_image("photo.jpg", background_color="white")
        >>>
        >>> # AI-generated background
        >>> result = client.edit_image(
        ...     "photo.jpg",
        ...     background_prompt="on a beach at sunset"
        ... )
        >>>
        >>> # Advanced: soft shadow + lighting adjustment
        >>> result = client.edit_image(
        ...     "product.jpg",
        ...     background_color="F5F5F5",
        ...     shadow_mode="ai.soft",
        ...     lighting_mode="ai.auto",
        ...     padding="0.1"
        ... )
        >>>
        >>> # Remove text from image
        >>> result = client.edit_image(
        ...     "image_with_watermark.jpg",
        ...     text_removal_mode="ai.artificial",
        ...     remove_background=False
        ... )
    """
    client = self._get_client()

    # Validate inputs
    if image_file is None and image_url is None:
        raise ValueError("Either image_file or image_url must be provided")
    if image_file is not None and image_url is not None:
        raise ValueError("Cannot provide both image_file and image_url")

    # Determine if using GET (URL) or POST (file)
    use_post = image_file is not None

    # Build parameters dictionary
    params: Dict[str, Any] = {}

    # Add all parameters, converting Python names to API names
    local_vars = locals()
    param_names = [
        "image_url",
        "remove_background",
        "background_color",
        "background_prompt",
        "background_image_url",
        "background_blur_mode",
        "background_blur_radius",
        "background_expand_prompt",
        "background_guidance_image_url",
        "background_guidance_scale",
        "background_negative_prompt",
        "background_scaling",
        "background_seed",
        "beautify_mode",
        "beautify_seed",
        "expand_mode",
        "expand_seed",
        "export_format",
        "export_dpi",
        "horizontal_alignment",
        "vertical_alignment",
        "ignore_padding_and_snap_on_cropped_sides",
        "image_from_prompt_prompt",
        "image_from_prompt_seed",
        "image_from_prompt_size",
        "keep_existing_alpha_channel",
        "preserve_metadata",
        "layers",
        "lighting_mode",
        "margin",
        "margin_bottom",
        "margin_left",
        "margin_right",
        "margin_top",
        "max_height",
        "max_width",
        "output_size",
        "padding",
        "padding_bottom",
        "padding_left",
        "padding_right",
        "padding_top",
        "reference_box",
        "scaling",
        "segmentation_mode",
        "segmentation_negative_prompt",
        "segmentation_prompt",
        "shadow_mode",
        "template_id",
        "text_removal_mode",
        "uncrop_mode",
        "uncrop_seed",
        "upscale_mode",
    ]

    for param_name in param_names:
        value = local_vars.get(param_name)
        if value is not None:
            api_name = normalize_param_name(param_name)
            params[api_name] = value

    # Make request
    if use_post:
        # Load and validate main image file if path is provided
        if isinstance(image_file, (str, Path)):
            image_data = load_image_file(
                image_file,
                validate=self.validate_images,
                auto_resize=self.auto_resize,
                auto_convert=self.auto_convert,
            )
            filename = Path(image_file).name
        else:
            # For bytes input, validate if enabled
            if self.validate_images:
                from ..validation import validate_and_prepare_image
                image_data = validate_and_prepare_image(
                    image_file,
                    auto_resize=self.auto_resize,
                    auto_convert=self.auto_convert,
                    validate=True,
                )
            else:
                image_data = image_file
            filename = "image.jpg"

        # Build multipart form data
        files = {
            "imageFile": (filename, image_data, "image/jpeg"),
        }

        # Add and validate background image file if provided
        if background_image_file is not None:
            if isinstance(background_image_file, (str, Path)):
                bg_data = load_image_file(
                    background_image_file,
                    validate=self.validate_images,
                    auto_resize=self.auto_resize,
                    auto_convert=self.auto_convert,
                )
                bg_filename = Path(background_image_file).name
            else:
                if self.validate_images:
                    from ..validation import validate_and_prepare_image
                    bg_data = validate_and_prepare_image(
                        background_image_file,
                        auto_resize=self.auto_resize,
                        auto_convert=self.auto_convert,
                        validate=True,
                    )
                else:
                    bg_data = background_image_file
                bg_filename = "background.jpg"
            files["background.imageFile"] = (bg_filename, bg_data, "image/jpeg")

        # Add and validate guidance image file if provided
        if background_guidance_image_file is not None:
            if isinstance(background_guidance_image_file, (str, Path)):
                guide_data = load_image_file(
                    background_guidance_image_file,
                    validate=self.validate_images,
                    auto_resize=self.auto_resize,
                    auto_convert=self.auto_convert,
                )
                guide_filename = Path(background_guidance_image_file).name
            else:
                if self.validate_images:
                    from ..validation import validate_and_prepare_image
                    guide_data = validate_and_prepare_image(
                        background_guidance_image_file,
                        auto_resize=self.auto_resize,
                        auto_convert=self.auto_convert,
                        validate=True,
                    )
                else:
                    guide_data = background_guidance_image_file
                guide_filename = "guidance.jpg"
            files["background.guidance.imageFile"] = (
                guide_filename,
                guide_data,
                "image/jpeg",
            )

        # Validate upscale mode dimensions if upscale is enabled
        if upscale_mode is not None and self.validate_images:
            from ..validation import validate_upscale_dimensions
            validate_upscale_dimensions(image_data, upscale_mode)

        response = self._make_request_with_retry(
            "POST",
            f"{self.IMAGE_API_BASE_URL}/v2/edit",
            files=files,
            data=params,
        )
    else:
        # GET request with URL
        response = self._make_request_with_retry(
            "GET",
            f"{self.IMAGE_API_BASE_URL}/v2/edit",
            params=params,
        )

    # Handle response
    result = self._handle_response(response, expect_json=False)

    # Save to file if requested
    if output_file is not None:
        result.save(output_file)

    return result


async def aedit_image(
    self: "PhotoRoomClient",
    image_file: Optional[Union[str, Path, bytes]] = None,
    image_url: Optional[str] = None,
    # Background parameters
    remove_background: Optional[bool] = True,
    background_color: Optional[str] = None,
    background_prompt: Optional[str] = None,
    background_image_url: Optional[str] = None,
    background_image_file: Optional[Union[str, Path, bytes]] = None,
    background_blur_mode: Optional[Literal["gaussian", "bokeh"]] = None,
    background_blur_radius: Optional[float] = None,
    background_expand_prompt: Optional[str] = None,
    background_guidance_image_url: Optional[str] = None,
    background_guidance_image_file: Optional[Union[str, Path, bytes]] = None,
    background_guidance_scale: Optional[float] = None,
    background_negative_prompt: Optional[str] = None,
    background_scaling: Optional[Literal["fit", "fill"]] = None,
    background_seed: Optional[int] = None,
    # Beautify parameters
    beautify_mode: Optional[Literal["ai.auto", "ai.food"]] = None,
    beautify_seed: Optional[int] = None,
    # Expand parameters
    expand_mode: Optional[Literal["ai.auto"]] = None,
    expand_seed: Optional[int] = None,
    # Export parameters
    export_format: Optional[Literal["png", "jpeg", "jpg", "webp"]] = "png",
    export_dpi: Optional[int] = None,
    # Positioning parameters
    horizontal_alignment: Optional[Literal["left", "center", "right"]] = None,
    vertical_alignment: Optional[Literal["top", "center", "bottom"]] = None,
    ignore_padding_and_snap_on_cropped_sides: Optional[bool] = None,
    # Image from prompt
    image_from_prompt_prompt: Optional[str] = None,
    image_from_prompt_seed: Optional[int] = None,
    image_from_prompt_size: Optional[
        Literal[
            "LANDSCAPE_16_9",
            "LANDSCAPE_4_3",
            "PORTRAIT_16_9",
            "PORTRAIT_4_3",
            "SQUARE_HD",
        ]
    ] = None,
    # Metadata
    keep_existing_alpha_channel: Optional[Literal["auto", "never"]] = None,
    preserve_metadata: Optional[Literal["never", "xmp", "exifSubset"]] = None,
    # Layers
    layers: Optional[Dict[str, Any]] = None,
    # Lighting
    lighting_mode: Optional[
        Literal["ai.auto", "ai.preserve-hue-and-saturation"]
    ] = None,
    # Size and padding parameters
    margin: Optional[PaddingMarginSpec] = None,
    margin_bottom: Optional[PaddingMarginSpec] = None,
    margin_left: Optional[PaddingMarginSpec] = None,
    margin_right: Optional[PaddingMarginSpec] = None,
    margin_top: Optional[PaddingMarginSpec] = None,
    max_height: Optional[int] = None,
    max_width: Optional[int] = None,
    output_size: Optional[str] = None,
    padding: Optional[PaddingMarginSpec] = None,
    padding_bottom: Optional[PaddingMarginSpec] = None,
    padding_left: Optional[PaddingMarginSpec] = None,
    padding_right: Optional[PaddingMarginSpec] = None,
    padding_top: Optional[PaddingMarginSpec] = None,
    # Reference and scaling
    reference_box: Optional[Literal["subjectBox", "originalImage"]] = None,
    scaling: Optional[Literal["fit", "fill"]] = None,
    # Segmentation
    segmentation_mode: Optional[
        Literal["keepSalientObject", "ignoreSalientObject"]
    ] = None,
    segmentation_negative_prompt: Optional[str] = None,
    segmentation_prompt: Optional[str] = None,
    # Shadow
    shadow_mode: Optional[Literal["ai.soft", "ai.hard", "ai.floating"]] = None,
    # Template
    template_id: Optional[str] = None,
    # Text removal
    text_removal_mode: Optional[Literal["ai.artificial", "ai.natural", "ai.all"]] = None,
    # Uncrop
    uncrop_mode: Optional[Literal["ai.auto"]] = None,
    uncrop_seed: Optional[int] = None,
    # Upscale
    upscale_mode: Optional[Literal["ai.fast", "ai.slow"]] = None,
    # Output
    output_file: Optional[Union[str, Path]] = None,
) -> ImageResponse:
    """Edit an image with AI-powered transformations (async).

    Async version of edit_image(). See edit_image() for full documentation.

    Examples:
        >>> async with PhotoRoomClient(async_mode=True) as client:
        ...     result = await client.edit_image(
        ...         "photo.jpg",
        ...         background_prompt="on a beach"
        ...     )
        ...     result.save("output.png")
    """
    client = self._get_client()

    # Validate inputs
    if image_file is None and image_url is None:
        raise ValueError("Either image_file or image_url must be provided")
    if image_file is not None and image_url is not None:
        raise ValueError("Cannot provide both image_file and image_url")

    # Determine if using GET (URL) or POST (file)
    use_post = image_file is not None

    # Build parameters dictionary
    params: Dict[str, Any] = {}

    # Add all parameters
    local_vars = locals()
    param_names = [
        "image_url",
        "remove_background",
        "background_color",
        "background_prompt",
        "background_image_url",
        "background_blur_mode",
        "background_blur_radius",
        "background_expand_prompt",
        "background_guidance_image_url",
        "background_guidance_scale",
        "background_negative_prompt",
        "background_scaling",
        "background_seed",
        "beautify_mode",
        "beautify_seed",
        "expand_mode",
        "expand_seed",
        "export_format",
        "export_dpi",
        "horizontal_alignment",
        "vertical_alignment",
        "ignore_padding_and_snap_on_cropped_sides",
        "image_from_prompt_prompt",
        "image_from_prompt_seed",
        "image_from_prompt_size",
        "keep_existing_alpha_channel",
        "preserve_metadata",
        "layers",
        "lighting_mode",
        "margin",
        "margin_bottom",
        "margin_left",
        "margin_right",
        "margin_top",
        "max_height",
        "max_width",
        "output_size",
        "padding",
        "padding_bottom",
        "padding_left",
        "padding_right",
        "padding_top",
        "reference_box",
        "scaling",
        "segmentation_mode",
        "segmentation_negative_prompt",
        "segmentation_prompt",
        "shadow_mode",
        "template_id",
        "text_removal_mode",
        "uncrop_mode",
        "uncrop_seed",
        "upscale_mode",
    ]

    for param_name in param_names:
        value = local_vars.get(param_name)
        if value is not None:
            api_name = normalize_param_name(param_name)
            params[api_name] = value

    # Make request
    if use_post:
        # Load and validate main image file if path is provided
        if isinstance(image_file, (str, Path)):
            image_data = load_image_file(
                image_file,
                validate=self.validate_images,
                auto_resize=self.auto_resize,
                auto_convert=self.auto_convert,
            )
            filename = Path(image_file).name
        else:
            # For bytes input, validate if enabled
            if self.validate_images:
                from ..validation import validate_and_prepare_image
                image_data = validate_and_prepare_image(
                    image_file,
                    auto_resize=self.auto_resize,
                    auto_convert=self.auto_convert,
                    validate=True,
                )
            else:
                image_data = image_file
            filename = "image.jpg"

        # Build multipart form data
        files = {
            "imageFile": (filename, image_data, "image/jpeg"),
        }

        # Add and validate background image file if provided
        if background_image_file is not None:
            if isinstance(background_image_file, (str, Path)):
                bg_data = load_image_file(
                    background_image_file,
                    validate=self.validate_images,
                    auto_resize=self.auto_resize,
                    auto_convert=self.auto_convert,
                )
                bg_filename = Path(background_image_file).name
            else:
                if self.validate_images:
                    from ..validation import validate_and_prepare_image
                    bg_data = validate_and_prepare_image(
                        background_image_file,
                        auto_resize=self.auto_resize,
                        auto_convert=self.auto_convert,
                        validate=True,
                    )
                else:
                    bg_data = background_image_file
                bg_filename = "background.jpg"
            files["background.imageFile"] = (bg_filename, bg_data, "image/jpeg")

        # Add and validate guidance image file if provided
        if background_guidance_image_file is not None:
            if isinstance(background_guidance_image_file, (str, Path)):
                guide_data = load_image_file(
                    background_guidance_image_file,
                    validate=self.validate_images,
                    auto_resize=self.auto_resize,
                    auto_convert=self.auto_convert,
                )
                guide_filename = Path(background_guidance_image_file).name
            else:
                if self.validate_images:
                    from ..validation import validate_and_prepare_image
                    guide_data = validate_and_prepare_image(
                        background_guidance_image_file,
                        auto_resize=self.auto_resize,
                        auto_convert=self.auto_convert,
                        validate=True,
                    )
                else:
                    guide_data = background_guidance_image_file
                guide_filename = "guidance.jpg"
            files["background.guidance.imageFile"] = (
                guide_filename,
                guide_data,
                "image/jpeg",
            )

        response = await self._make_request_with_retry_async(
            "POST",
            f"{self.IMAGE_API_BASE_URL}/v2/edit",
            files=files,
            data=params,
        )
    else:
        # GET request with URL
        response = await self._make_request_with_retry_async(
            "GET",
            f"{self.IMAGE_API_BASE_URL}/v2/edit",
            params=params,
        )

    # Handle response
    result = self._handle_response(response, expect_json=False)

    # Save to file if requested
    if output_file is not None:
        result.save(output_file)

    return result
