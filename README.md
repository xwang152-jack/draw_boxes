# Image Bounding Box Plugin

**Author:** xwang152-jack  
**Version:** 1.0.0  
**Type:** Tool Plugin  
**Contact:** xwang152@163.com

## Overview

A Dify tool plugin for image annotation visualization. It receives image data and annotation information from vision models, then returns images with drawn annotations. Perfect for visualizing object detection and image segmentation results.

## Key Features

- **Annotation Drawing**: Draw bounding boxes and labels on images
- **Flexible Coordinates**: Support both relative (0-1000) and absolute (pixel) coordinates
- **Custom Styling**: Customizable colors, line width, and font size
- **Multiple Formats**: Support various image and annotation formats
- **Error Handling**: Comprehensive parameter validation

## Supported Image Formats

### Dify File Object (Recommended)
```json
{
  "#files#": [
    {
      "dify_model_identity": "__dify__file__",
      "extension": ".jpeg",
      "filename": "example.jpeg",
      "mime_type": "image/jpeg", 
      "url": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...",
      "type": "image"
    }
  ]
}
```

### Traditional Formats
- **Base64 with prefix**: `data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...`
- **Pure Base64**: `/9j/4AAQSkZJRgABAQAAAQABAAD...`
- **URL**: `https://example.com/image.jpg`

## Parameters

### Required
| Parameter | Type | Description |
|-----------|------|-------------|
| `image_data` | string | Image data (URL or Base64) |
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

## Usage Examples

### Basic Usage
```python
result = image_mark_tool.invoke({
    "image_data": "https://example.com/image.jpg",
    "annotations": '''
    {
      "annotations": [
        {
          "bbox": [100, 100, 300, 200],
          "label": "cat",
          "confidence": 0.95
        }
      ]
    }
    '''
})
```

### Custom Styling with Absolute Coordinates
```python
result = image_mark_tool.invoke({
    "image_data": base64_image,
    "annotations": annotations,
    "coordinate_type": "absolute",
    "box_color": "#00ff00",
    "text_color": "#000000",
    "line_width": 3,
    "font_size": 20
})
```

## Output Format

**Success:**
```json
{
  "success": true,
  "result_image_base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "annotation_count": 2,
  "image_size": {"width": 800, "height": 600},
  "message": "Successfully drew 2 annotations"
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

## Installation

```bash
pip install -r requirements.txt
```

## License

See [PRIVACY.md](PRIVACY.md) for privacy policy.

## Changelog

### v1.0.0 (2025-09-27)
- Full Dify file object support
- Relative and absolute coordinate modes
- Smart format detection
- Production-ready release

## Support

Contact: xwang152@163.com or submit an issue.



