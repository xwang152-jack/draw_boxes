# Image Bounding Box Plugin

**Author:** xwang152-jack  
**Version:** 1.2.0  
**Type:** Tool Plugin  
**Contact:** xwang152@163.com

## Overview

A Dify tool plugin for image annotation visualization. It receives image files and annotation information, then returns images with drawn bounding boxes and labels. Perfect for visualizing object detection and image segmentation results.

## Key Features

- **Annotation Drawing**: Draw bounding boxes and labels on images
- **Dify File Support**: Native support for Dify file objects (recommended)
- **Flexible Coordinates**: Support both relative (0-1000) and absolute (pixel) coordinates
- **CJK Font Support**: Optimized font loading for Chinese/Japanese/Korean labels
- **Custom Styling**: Customizable colors, line width, and font size
- **Error Handling**: Comprehensive parameter validation

## Parameters

### Required
| Parameter | Type | Description |
|-----------|------|-------------|
| `image_file` | file | Image file to annotate |
| `annotations` | string | Annotation data (JSON string) |

### Optional
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `box_color` | string | `#ff0000` | Bounding box color (hex) |
| `text_color` | string | `#ffffff` | Text color (hex) |
| `line_width` | number | `2` | Line width (1-20) |
| `font_size` | number | `16` | Font size (8-72) |
| `coordinate_type` | string | `relative` | Coordinate type: `relative` or `absolute` |

## Annotation Format

```json
{
  "annotations": [
    {
      "bbox": [x1, y1, x2, y2],
      "label": "person",
      "confidence": 0.95
    }
  ]
}
```

### Coordinate Types

**Relative Coordinates (0-1000)**:
- `bbox`: [100, 200, 300, 400] → converted to pixel coordinates
- Default mode for better compatibility

**Absolute Coordinates (pixels)**:
- `bbox`: [50, 100, 150, 200] → used directly as pixel coordinates
- Set `coordinate_type: "absolute"` to use this mode

## Usage in Dify Workflow

1. Add the "Image Bounding Box" tool node to your workflow
2. Connect an image file to the `image_file` parameter
3. Provide annotation JSON from a vision model or other source
4. The tool outputs an annotated image with bounding boxes

## Output Format

**Success:**
```json
{
  "success": true,
  "annotation_count": 2,
  "image_size": {"width": 800, "height": 600},
  "message": "成功绘制2个标注"
}
```

**Error:**
```json
{
  "success": false,
  "error": "Error description",
  "error_code": 400
}
```

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Parameter error |
| 404 | Image loading failed |
| 413 | Image too large (>4096x4096) |
| 422 | Invalid annotation format |
| 500 | Internal server error |

## Limitations

- Maximum image size: 4096x4096 pixels
- Maximum annotations: 100 per image
- Line width range: 1-20
- Font size range: 8-72

## CJK Font Support

For proper Chinese/Japanese/Korean label display, ensure your Dify environment has CJK fonts installed:

```bash
# Debian/Ubuntu
apt-get install -y fonts-noto-cjk

# Alpine Linux
apk add font-noto-cjk
```

## Installation

```bash
pip install -r requirements.txt
```

## License

See [PRIVACY.md](PRIVACY.md) for privacy policy.

## Changelog

### v1.2.0 (2025-12-07)
- **Breaking Change**: Changed `image_data` (string) to `image_file` (file type) for better Dify integration
- Added native Dify File object support
- Improved CJK font loading priority for Chinese/Japanese/Korean labels
- Enhanced debug logging for troubleshooting

### v1.1.1
- Bug fixes and stability improvements

### v1.0.0 (2025-09-27)
- Initial release
- Relative and absolute coordinate modes
- Smart format detection

## Support

Contact: xwang152@163.com or submit an issue.
