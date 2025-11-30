# PhotoRoom Python SDK

A modern, fully-typed Python SDK for the [PhotoRoom API](https://www.photoroom.com/api). Remove backgrounds, edit images with AI, and enhance product photos with a simple Python interface.

📖 **[View Full Documentation](https://and1ds.github.io/photoroom-python/docs.html)**

## Features

- **Background Removal**: Remove backgrounds with award-winning AI
- **AI Backgrounds**: Generate backgrounds from text prompts
- **Image Enhancement**: Shadows, lighting, upscaling, text removal, and more
- **Image Validation**: Automatic validation, resizing, and format conversion
- **Sync & Async**: Full support for both synchronous and asynchronous operations
- **Type Safe**: Complete type hints for excellent IDE support
- **Comprehensive**: 50+ parameters for fine-grained control
- **Automatic Retry**: Built-in exponential backoff for transient errors

## Installation

```bash
pip install photoroom
```

Or with poetry:

```bash
poetry add photoroom
```

## Quick Start

### Authentication

Get your API key from the [PhotoRoom API Dashboard](https://app.photoroom.com/api).

```python
from photoroom import PhotoRoomClient

# Option 1: Pass API key directly
client = PhotoRoomClient(api_key="your_api_key")

# Option 2: Set environment variable
# export PHOTOROOM_API_KEY=your_api_key
client = PhotoRoomClient()
```

**Sandbox API Keys:**

If you're using a sandbox API key (starts with `sandbox_`), note that some endpoints like `get_account()` may not be available. The SDK will show a warning when a sandbox key is detected. For full functionality, use a production API key.

```python
# Check if using sandbox key
if client.is_sandbox:
    print("Using sandbox API key - some features may be limited")
```

### Remove Background

```python
# Simple background removal
result = client.remove_background("photo.jpg")
result.save("output.png")

# With white background
result = client.remove_background(
    "photo.jpg",
    bg_color="white",
    output_file="output.png"
)

# High-quality mode with cropping
result = client.remove_background(
    "photo.jpg",
    size="hd",
    crop=True,
    format="png"
)
```

### Edit Images

```python
# Add white background with soft shadow
result = client.edit_image(
    image_file="product.jpg",
    background_color="white",
    shadow_mode="ai.soft",
    padding=0.1
)
result.save("enhanced_product.png")

# AI-generated background
result = client.edit_image(
    image_file="person.jpg",
    background_prompt="on a beach at sunset",
    shadow_mode="ai.soft"
)

# Advanced editing: lighting + shadow + custom size
result = client.edit_image(
    image_file="product.jpg",
    background_color="F5F5F5",
    lighting_mode="ai.auto",
    shadow_mode="ai.soft",
    padding="15%",
    output_size="2048x2048",
    export_format="png",
    export_dpi=300
)
```

### Remove Text

```python
# Remove artificial text (watermarks, logos)
result = client.edit_image(
    image_file="watermarked.jpg",
    text_removal_mode="ai.artificial",
    remove_background=False
)

# Check how many texts were detected
print(f"Detected {result.texts_detected} texts")
```

### Upscale Images

```python
# Fast 4x upscaling
result = client.edit_image(
    image_file="small_image.jpg",
    upscale_mode="ai.fast",
    remove_background=False
)

# High-quality upscaling (slower)
result = client.edit_image(
    image_file="small_image.jpg",
    upscale_mode="ai.slow",
    remove_background=False
)
```

### Product Photo Enhancement

```python
# Beautify product images
result = client.edit_image(
    image_file="raw_product.jpg",
    beautify_mode="ai.auto",
    background_color="white",
    shadow_mode="ai.soft",
    padding=0.15
)

# Food-specific enhancement
result = client.edit_image(
    image_file="food.jpg",
    beautify_mode="ai.food",
    background_color="white"
)
```

### Check Account Quota

```python
account = client.get_account()
print(f"Plan: {account.plan}")
print(f"Images available: {account.images.available}/{account.images.subscription}")
```

## Async Usage

All methods have async equivalents:

```python
import asyncio
from photoroom import PhotoRoomClient

async def main():
    async with PhotoRoomClient(async_mode=True) as client:
        # Remove background (async)
        result = await client.remove_background("photo.jpg")
        result.save("output.png")

        # Edit image (async)
        result = await client.edit_image(
            image_file="photo.jpg",
            background_prompt="in a professional studio"
        )

        # Get account (async)
        account = await client.get_account()
        print(f"Plan: {account.plan}")

asyncio.run(main())
```

## Advanced Features

### Custom Segmentation

```python
# Keep specific objects
result = client.edit_image(
    image_file="complex_scene.jpg",
    segmentation_prompt="keep the car",
    segmentation_mode="keepSalientObject"
)

# Remove specific objects
result = client.edit_image(
    image_file="photo.jpg",
    segmentation_prompt="remove the background objects",
    segmentation_negative_prompt="person"
)
```

### Background Guidance

```python
# Use a reference image to guide AI background generation
result = client.edit_image(
    image_file="product.jpg",
    background_prompt="professional studio",
    background_guidance_image_file="reference_bg.jpg",
    background_guidance_scale=0.8
)
```

### Reproducible Results

```python
# Use seeds for consistent results
seed = 42

result1 = client.edit_image(
    image_file="photo.jpg",
    background_prompt="on a beach",
    background_seed=seed
)

result2 = client.edit_image(
    image_file="photo.jpg",
    background_prompt="on a beach",
    background_seed=seed
)
# result1 and result2 will have the same background
```

### Response Metadata

```python
result = client.edit_image(
    image_file="photo.jpg",
    background_prompt="in a forest"
)

# Access image data and size
print(f"Size: {result.size} bytes ({result.size_kb:.1f} KB)")

# Access metadata
print(f"Background seed: {result.background_seed}")
print(f"Texts detected: {result.texts_detected}")
print(f"Edit further URL: {result.edit_further_url}")
print(f"Unsupported attributes: {result.unsupported_attributes}")
```

## Retry and Resilience

The SDK automatically retries failed requests with exponential backoff to handle transient server errors.

### Default Behavior

By default, the SDK will:
- Retry up to **3 times** on server errors (500, 502, 503, 504)
- Use **exponential backoff** with jitter (waits 1s, 2s, 4s between retries)
- **Not retry** on client errors (400, 401, 403, etc.)
- Retry on **network errors** (connection failures, timeouts)

```python
# Default retry behavior - automatically retries server errors
client = PhotoRoomClient(api_key="your_api_key")

# If the server returns 500/503, the SDK will retry automatically
result = client.remove_background("photo.jpg")
```

### Custom Retry Configuration

Customize retry behavior for your use case:

```python
client = PhotoRoomClient(
    api_key="your_api_key",
    max_retries=5,                          # Retry up to 5 times
    retry_backoff=3.0,                      # 3x backoff (3s, 9s, 27s, ...)
    retry_on_status=[500, 502, 503, 504]    # Which status codes to retry
)
```

### Disable Retries

For maximum control, disable automatic retries:

```python
# No automatic retries
client = PhotoRoomClient(
    api_key="your_api_key",
    max_retries=0
)
```

### How It Works

The retry logic uses exponential backoff with jitter to avoid thundering herd problems:

1. **First attempt** fails with 503 Service Unavailable
2. **Wait ~1 second** (with random jitter)
3. **Second attempt** fails with 503
4. **Wait ~2 seconds** (with random jitter)
5. **Third attempt** succeeds ✓

If all retries are exhausted, the SDK raises the appropriate exception (e.g., `PhotoRoomServerError`).

## Image Validation

The SDK provides comprehensive image validation to ensure images meet PhotoRoom API requirements before upload. This helps catch issues early and can automatically fix common problems.

### API Limits

PhotoRoom has the following limits:
- **Maximum file size**: 30 MB
- **Maximum dimension**: 5000 pixels on widest side
- **Recommended megapixels**: 25 MP for optimal performance
- **Supported formats**: PNG, JPEG/JPG, WebP
- **Upscale mode limits**:
  - `ai.fast`: Maximum 1000×1000 pixels input
  - `ai.slow`: Maximum 512×512 pixels input

### Default Behavior

By default, validation is **enabled** for all image uploads:

```python
# Validation is ON by default
client = PhotoRoomClient(api_key="your_api_key")

# This will validate the image meets API requirements
result = client.remove_background("photo.jpg")
```

Validation checks:
- ✅ File format is supported (PNG, JPEG, WebP)
- ✅ File size ≤ 30 MB
- ✅ Resolution ≤ 5000 pixels on widest side
- ✅ Upscale mode dimension limits (if applicable)

If validation fails, an `ImageValidationError` is raised with a helpful message:

```python
from photoroom import ImageValidationError

try:
    result = client.remove_background("huge_image.jpg")
except ImageValidationError as e:
    print(f"Validation failed: {e}")
    # Example: "Image size (35.2MB) exceeds maximum allowed size (30MB).
    #           Consider using auto_resize=True to automatically resize large images."
```

### Auto-Resize Large Images

Enable `auto_resize` to automatically resize images that exceed size or dimension limits:

```python
# Auto-resize images that are too large
client = PhotoRoomClient(
    api_key="your_api_key",
    validate_images=True,
    auto_resize=True
)

# This 50MB, 8000×6000 image will be automatically resized
# to fit within 30MB and 5000px limits
result = client.remove_background("huge_photo.jpg")
```

How it works:
- Images exceeding 5000px are resized to fit within the dimension limit
- Images exceeding 30MB are compressed using binary search optimization
- Aspect ratio is always preserved
- Quality is maintained at 85% JPEG quality
- Requires **Pillow** library: `pip install Pillow`

### Auto-Convert Unsupported Formats

Enable `auto_convert` to automatically convert unsupported formats to WebP:

```python
# Auto-convert HEIC, TIFF, BMP, etc. to WebP
client = PhotoRoomClient(
    api_key="your_api_key",
    validate_images=True,
    auto_convert=True
)

# These formats will be automatically converted to WebP:
# HEIC, HEIF, TIFF, TIF, BMP, GIF, ICO
result = client.remove_background("photo.heic")  # Converted to WebP
result = client.remove_background("scan.tiff")   # Converted to WebP
```

Conversion details:
- Target format: **WebP** (excellent compression and quality)
- Quality: 90% (configurable in validation module)
- Transparency preserved for RGBA images
- Requires **Pillow** library: `pip install Pillow`

### Combined: Auto-Resize + Auto-Convert

Enable both for maximum compatibility:

```python
# Handle all image issues automatically
client = PhotoRoomClient(
    api_key="your_api_key",
    validate_images=True,
    auto_resize=True,
    auto_convert=True
)

# This will:
# 1. Convert HEIC to WebP
# 2. Resize if needed to fit within limits
# 3. Upload successfully
result = client.remove_background("iphone_photo.heic")
```

### Disable Validation

For maximum control or when you're sure images are valid, disable validation:

```python
# No validation - upload as-is
client = PhotoRoomClient(
    api_key="your_api_key",
    validate_images=False
)

# Images are uploaded without any checks
result = client.remove_background("photo.jpg")
```

⚠️ **Warning**: Disabling validation may cause API errors if images don't meet requirements.

### Upscale Mode Validation

When using upscale modes, the SDK automatically validates input dimensions:

```python
client = PhotoRoomClient(api_key="your_api_key", validate_images=True)

# ai.fast requires input ≤ 1000×1000
try:
    result = client.edit_image(
        image_file="large_photo.jpg",  # 2000×1500
        upscale_mode="ai.fast"
    )
except ImageValidationError as e:
    print(e)
    # "Image resolution (2000x1500) exceeds maximum for ai.fast upscale mode.
    #  Maximum allowed: 1000x1000px."

# ai.slow requires input ≤ 512×512
result = client.edit_image(
    image_file="small_photo.jpg",  # 500×400
    upscale_mode="ai.slow"  # ✓ Valid
)
```

### Validation Error Types

```python
from photoroom import ImageValidationError

try:
    result = client.remove_background("image.xyz")
except ImageValidationError as e:
    # Common validation errors:
    # - "Unsupported image format: xyz. Supported formats: png, jpg, jpeg, webp"
    # - "Image size (35.2MB) exceeds maximum allowed size (30MB)"
    # - "Image resolution (6000x4000) exceeds maximum dimension of 5000px"
    # - "Image resolution (1200x800) exceeds maximum for ai.fast upscale mode"
    # - "Image data is empty"
    # - "PIL/Pillow is required for auto-resize functionality"
    print(f"Validation failed: {e}")
```

### Best Practices

1. **Keep validation enabled** - Catches issues before they become API errors
2. **Enable auto-resize for user uploads** - Handles photos from modern cameras/phones
3. **Enable auto-convert for mobile apps** - iOS HEIC photos are common
4. **Install Pillow for full functionality**:
   ```bash
   pip install photoroom[validation]
   # or
   pip install Pillow
   ```
5. **Use appropriate upscale modes**:
   - `ai.fast` for quick 4x upscaling (input ≤ 1000×1000)
   - `ai.slow` for best quality (input ≤ 512×512)

### Example: Production Configuration

```python
from photoroom import PhotoRoomClient, ImageValidationError

# Recommended production setup
client = PhotoRoomClient(
    api_key="your_api_key",
    validate_images=True,      # Catch issues early
    auto_resize=True,          # Handle large images
    auto_convert=True,         # Handle all formats
    max_retries=3,             # Retry on server errors
    timeout=120.0              # 2 minute timeout
)

# Robust error handling
try:
    result = client.remove_background(
        user_uploaded_file,
        bg_color="white",
        output_file="output.png"
    )
    print(f"Success! Saved to output.png ({result.size_kb:.1f} KB)")
except ImageValidationError as e:
    print(f"Image validation failed: {e}")
except Exception as e:
    print(f"Processing failed: {e}")
```

## Rate Limiting

The SDK includes built-in rate limiting to help you stay within API rate limits and avoid overwhelming the service.

### How It Works

Rate limiting uses a token bucket algorithm:
- Tokens refill at the specified rate (e.g., 10 tokens/second for `rate_limit=10.0`)
- Each request consumes 1 token
- If no tokens available, the SDK either waits (default) or raises an error

### Basic Usage

```python
from photoroom import PhotoRoomClient

# Limit to 5 requests per second
client = PhotoRoomClient(
    api_key="your_api_key",
    rate_limit=5.0,  # 5 requests/second
    rate_limit_strategy="wait"  # Wait for tokens (default)
)

# Make requests - automatically rate limited
for image in image_list:
    result = client.remove_background(image)
    result.save(f"output_{image}")
```

### Strategies

**1. "wait" Strategy (Default)**

Automatically sleeps until tokens are available:

```python
client = PhotoRoomClient(
    api_key="your_api_key",
    rate_limit=10.0,
    rate_limit_strategy="wait"  # Sleep until tokens available
)

# These will execute at max 10/second
for i in range(100):
    client.remove_background(f"image_{i}.jpg")
```

**2. "error" Strategy**

Raises `RateLimitError` when rate limit exceeded:

```python
from photoroom import PhotoRoomClient
from photoroom.rate_limiter import RateLimitError

client = PhotoRoomClient(
    api_key="your_api_key",
    rate_limit=10.0,
    rate_limit_strategy="error"  # Raise exception
)

try:
    # Fast loop - will hit rate limit
    for i in range(100):
        client.remove_background(f"image_{i}.jpg")
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
    # Handle rate limit (e.g., slow down, retry later)
```

### Async Rate Limiting

Rate limiting works with async clients too:

```python
import asyncio
from photoroom import PhotoRoomClient

async def process_images():
    async with PhotoRoomClient(
        api_key="your_api_key",
        async_mode=True,
        rate_limit=5.0,
        rate_limit_strategy="wait"
    ) as client:
        # Process images at max 5/second
        tasks = [
            client.aremove_background(f"image_{i}.jpg")
            for i in range(20)
        ]
        results = await asyncio.gather(*tasks)

asyncio.run(process_images())
```

### Disable Rate Limiting

Set `rate_limit=None` or `rate_limit=0` to disable:

```python
# No rate limiting
client = PhotoRoomClient(
    api_key="your_api_key",
    rate_limit=None  # Disabled
)
```

### Best Practices

1. **Conservative limits**: Start with `rate_limit=5.0` and increase if needed
2. **Monitor errors**: Watch for 429 (Too Many Requests) errors
3. **Combine with retries**: Use both rate limiting and retry logic:
   ```python
   client = PhotoRoomClient(
       api_key="your_api_key",
       rate_limit=10.0,       # Prevent exceeding limits
       max_retries=3,         # Retry on transient errors
       rate_limit_strategy="wait"
   )
   ```
4. **Batch processing**: For large batches, use conservative rate limits to avoid service disruption

### Common Rate Limits

Typical API rate limits (adjust based on your plan):
- **Development**: `rate_limit=1.0` (1 req/s)
- **Production**: `rate_limit=10.0` (10 req/s)
- **High-volume**: `rate_limit=20.0` (20 req/s)

Check your PhotoRoom plan for specific rate limits.

## Batch Processing

The SDK provides powerful batch processing capabilities to process multiple images efficiently with concurrency control, progress tracking, and error handling.

### Basic Usage

```python
from photoroom import PhotoRoomClient

client = PhotoRoomClient(api_key="your-api-key")

# Batch remove background from multiple images
inputs = ["photo1.jpg", "photo2.jpg", "photo3.jpg"]
result = client.batch_remove_background(
    inputs,
    bg_color="white",
    max_workers=3  # Process 3 images concurrently
)

print(f"Processed {result.success_count}/{result.total} images")
print(f"Success rate: {result.success_rate:.1%}")
print(f"Total time: {result.total_time:.2f}s")
```

### Async Batch Processing

```python
import asyncio
from photoroom import PhotoRoomClient

async def batch_process():
    async with PhotoRoomClient(api_key="your-api-key", async_mode=True) as client:
        inputs = ["photo1.jpg", "photo2.jpg", "photo3.jpg"]
        result = await client.abatch_remove_background(
            inputs,
            bg_color="white",
            max_concurrency=5  # Process up to 5 images concurrently
        )

        print(f"Processed {result.success_count}/{result.total} images")

asyncio.run(batch_process())
```

### Automatic Output Saving

Save all processed images automatically:

```python
result = client.batch_remove_background(
    ["photo1.jpg", "photo2.jpg", "photo3.jpg"],
    bg_color="white",
    output_dir="output/",
    output_pattern="{index}_processed_{name}"  # e.g., "0_processed_photo1.jpg"
)

# Or use just the index
result = client.batch_edit_image(
    inputs,
    background_prompt="on a beach",
    output_dir="edited/",
    output_pattern="{index}.png"  # e.g., "0.png", "1.png", "2.png"
)
```

### Progress Tracking

Monitor progress with a callback function:

```python
from photoroom import BatchProgress

def progress_callback(progress: BatchProgress):
    print(f"Progress: {progress.completed}/{progress.total} "
          f"({progress.progress_percent:.1f}%) - "
          f"Success: {progress.successful}, Failed: {progress.failed}")

    if progress.estimated_remaining_seconds:
        print(f"Estimated time remaining: {progress.estimated_remaining_seconds:.1f}s")

result = client.batch_remove_background(
    ["photo1.jpg", "photo2.jpg", "photo3.jpg"],
    progress_callback=progress_callback
)
```

### Error Handling Strategies

Control how errors are handled:

```python
# Continue on errors (default) - process all images even if some fail
result = client.batch_remove_background(
    inputs,
    on_error="continue"
)

# Fail fast - stop on first error
try:
    result = client.batch_remove_background(
        inputs,
        on_error="fail_fast"
    )
except BatchError as e:
    print(f"Batch failed: {e}")
```

### Working with Results

```python
result = client.batch_remove_background(["photo1.jpg", "photo2.jpg", "photo3.jpg"])

# Check overall success
if result.all_successful:
    print("All images processed successfully!")

# Get successful and failed results
for item in result.successful:
    print(f"Success: {item.input_file} -> {item.result.size_kb:.1f}KB")

for item in result.failed:
    print(f"Failed: {item.input_file} - Error: {item.error}")

# Raise exception if any failed
try:
    result.raise_on_failure()
except BatchPartialFailureError as e:
    print(f"{e.successful_count} succeeded, {e.failed_count} failed")
```

### Batch Edit Images

Process multiple images with editing operations:

```python
# AI background generation for multiple images
result = client.batch_edit_image(
    ["product1.jpg", "product2.jpg", "product3.jpg"],
    background_prompt="minimalist white studio background",
    background_seed=42,  # Same background for all
    padding="10%",
    max_workers=3
)

# Different parameters for each (manual loop)
images = ["shirt.jpg", "shoes.jpg", "hat.jpg"]
prompts = ["on model", "on display shelf", "on mannequin head"]

results = []
for img, prompt in zip(images, prompts):
    result = client.edit_image(img, background_prompt=prompt)
    results.append(result)
```

### Statistics and Analysis

```python
result = client.batch_remove_background(inputs, bg_color="white")

stats = result.get_statistics()
print(f"Total images: {stats['total']}")
print(f"Successful: {stats['successful']}")
print(f"Failed: {stats['failed']}")
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"Total time: {stats['total_time_seconds']:.2f}s")
print(f"Average time per image: {stats['average_time_per_item']:.2f}s")
```

### Batch Processing with Rate Limiting

Combine batch processing with rate limiting for optimal throughput:

```python
# Limit to 10 requests/second across all batch operations
client = PhotoRoomClient(
    api_key="your-api-key",
    rate_limit=10.0,
    rate_limit_strategy="wait"
)

# Process 100 images with 5 workers
# Rate limiter ensures we don't exceed 10 req/sec
result = client.batch_remove_background(
    images,
    max_workers=5,
    output_dir="output/"
)
```

### Best Practices

1. **Concurrency Control**: Set `max_workers` (sync) or `max_concurrency` (async) based on your system and rate limits
2. **Rate Limiting**: Always set appropriate rate limits to avoid API throttling
3. **Error Handling**: Use `on_error="continue"` for best-effort processing of large batches
4. **Progress Tracking**: Use callbacks for long-running batches to monitor progress
5. **Output Management**: Use `output_dir` and `output_pattern` for organized file management
6. **Memory Management**: For very large batches (1000+ images), consider processing in chunks

## API Reference

### PhotoRoomClient

Main client for interacting with the PhotoRoom API.

```python
client = PhotoRoomClient(
    api_key: Optional[str] = None,       # API key (or set PHOTOROOM_API_KEY env var)
    async_mode: bool = False,            # Use async client
    timeout: float = 120.0,              # Request timeout in seconds

    # Retry configuration
    max_retries: int = 3,                # Maximum retry attempts (default: 3)
    retry_backoff: float = 2.0,          # Exponential backoff factor (default: 2.0)
    retry_on_status: Optional[list] = None,  # Status codes to retry (default: [500, 502, 503, 504])

    # Rate limiting
    rate_limit: Optional[float] = None,  # Max requests per second
    rate_limit_strategy: str = "wait",   # "wait" (sleep) or "error" (raise exception)

    # Image validation
    validate_images: bool = True,        # Validate images before upload
    auto_resize: bool = False,           # Auto-resize large images
    auto_convert: bool = False           # Auto-convert unsupported formats to WebP
)
```

### remove_background()

Remove background from an image (/v1/segment endpoint).

**Parameters:**
- `image_file`: Image path or bytes
- `format`: Output format - "png", "jpg", "webp" (default: "png")
- `channels`: "rgba" or "alpha" (default: "rgba")
- `bg_color`: Background color (hex or name, e.g., "white", "FF0000")
- `size`: "preview", "medium", "hd", or "full" (default: "full")
- `crop`: Crop to cutout border (default: False)
- `despill`: Remove green screen reflections (default: False)
- `output_file`: Optional path to save result

### edit_image()

Edit image with AI transformations (/v2/edit endpoint).

**Core Parameters:**
- `image_file` / `image_url`: Input image (file or URL)
- `remove_background`: Remove background (default: True)
- `output_file`: Optional path to save result

**Background Parameters:**
- `background_color`: Background color (hex or name)
- `background_prompt`: AI background generation prompt
- `background_image_url` / `background_image_file`: Custom background
- `background_blur_mode`: "gaussian" or "bokeh"
- `background_blur_radius`: Blur amount (0-0.05)
- `background_seed`: Seed for reproducible backgrounds

**Enhancement Parameters:**
- `lighting_mode`: "ai.auto" or "ai.preserve-hue-and-saturation"
- `shadow_mode`: "ai.soft", "ai.hard", or "ai.floating"
- `beautify_mode`: "ai.auto" or "ai.food"
- `text_removal_mode`: "ai.artificial", "ai.natural", or "ai.all"
- `upscale_mode`: "ai.fast" or "ai.slow" (4x upscaling)
- `uncrop_mode`: "ai.auto"
- `expand_mode`: "ai.auto" (fill transparent pixels)

**Positioning Parameters:**
- `padding` / `margin`: General spacing (number, "30%", or "100px")
- `padding_top/bottom/left/right`: Side-specific padding
- `margin_top/bottom/left/right`: Side-specific margin
- `horizontal_alignment`: "left", "center", "right"
- `vertical_alignment`: "top", "center", "bottom"

**Export Parameters:**
- `export_format`: "png", "jpeg", "jpg", "webp" (default: "png")
- `export_dpi`: DPI value (72-1200)
- `output_size`: "auto", "WIDTHxHEIGHT", "originalImage", or "croppedSubject"
- `max_width` / `max_height`: Maximum dimensions

**Advanced Parameters:**
- `segmentation_prompt`: What to keep
- `segmentation_negative_prompt`: What to remove
- `template_id`: Template UUID
- `preserve_metadata`: "never", "xmp", or "exifSubset"
- `layers`: Advanced layer composition (dict)

See [full parameter documentation](https://docs.photoroom.com/image-editing-api) for details.

### get_account()

Get account information and quota.

**Returns:** `AccountInfo` with `plan` and `images` (available/subscription)

## Error Handling

```python
from photoroom import (
    PhotoRoomError,
    PhotoRoomBadRequest,
    PhotoRoomPaymentError,
    PhotoRoomAuthError,
    PhotoRoomServerError,
    ImageValidationError
)

try:
    result = client.remove_background("photo.jpg")
except ImageValidationError as e:
    print(f"Image validation failed: {e}")
except PhotoRoomAuthError:
    print("Invalid API key")
except PhotoRoomPaymentError:
    print("Quota exceeded")
except PhotoRoomBadRequest as e:
    print(f"Invalid parameters: {e.message}")
except PhotoRoomServerError:
    print("Server error, please retry")
except PhotoRoomError as e:
    print(f"API error: {e}")
```

## Testing

```bash
# Run unit tests (mocked, no API calls)
pytest

# Run integration tests (real API calls - uses quota!)
pytest -m integration

# Run with coverage
pytest --cov=photoroom --cov-report=html
```

## Development

```bash
# Install development dependencies
poetry install

# Format code
black photoroom tests

# Sort imports
isort photoroom tests

# Type checking
mypy photoroom

# Linting
flake8 photoroom tests
```

## Requirements

- Python ≥ 3.9
- httpx
- python-dotenv (optional)
- pydantic (optional, for type validation)

## License

MIT License - see LICENSE file for details

## Links

- [PhotoRoom API Documentation](https://docs.photoroom.com)
- [API Dashboard](https://app.photoroom.com/api)
- [Get API Key](https://app.photoroom.com/api)

## Support

For API issues, contact PhotoRoom support or visit the [documentation](https://docs.photoroom.com).
