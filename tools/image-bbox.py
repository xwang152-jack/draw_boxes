import base64
import json
import requests
from io import BytesIO
from collections.abc import Generator
from typing import Any

from PIL import Image, ImageDraw, ImageFont
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class ImageMarkTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        try:
            # 获取参数
            image_data = tool_parameters.get('image_data', '')
            annotations_str = tool_parameters.get('annotations', '')
            box_color = tool_parameters.get('box_color', '#ff0000')
            text_color = tool_parameters.get('text_color', '#ffffff')
            line_width = int(tool_parameters.get('line_width', 2))
            font_size = int(tool_parameters.get('font_size', 16))
            coordinate_type = tool_parameters.get('coordinate_type', 'relative')
            
            # 验证必需参数
            if not image_data:
                yield self.create_json_message({
                    "success": False,
                    "error": "image_data parameter is required",
                    "error_code": 400
                })
                return
                
            if not annotations_str:
                yield self.create_json_message({
                    "success": False,
                    "error": "annotations parameter is required",
                    "error_code": 400
                })
                return
            
            # 验证参数范围
            if line_width < 1 or line_width > 20:
                yield self.create_json_message({
                    "success": False,
                    "error": "line_width must be between 1 and 20",
                    "error_code": 400
                })
                return
                
            if font_size < 8 or font_size > 72:
                yield self.create_json_message({
                    "success": False,
                    "error": "font_size must be between 8 and 72",
                    "error_code": 400
                })
                return
            
            # 验证颜色格式
            if not self._is_valid_color(box_color):
                yield self.create_json_message({
                    "success": False,
                    "error": "Invalid box_color format. Use hex format like #ff0000",
                    "error_code": 400
                })
                return
                
            if not self._is_valid_color(text_color):
                yield self.create_json_message({
                    "success": False,
                    "error": "Invalid text_color format. Use hex format like #ffffff",
                    "error_code": 400
                })
                return
            
            # 加载图像
            image = self._load_image(image_data)
            if image is None:
                yield self.create_json_message({
                    "success": False,
                    "error": "Failed to load image. The image URL may be invalid, rate-limited, or inaccessible. Please check the image URL or try a different image source.",
                    "error_code": 404
                })
                return
            
            # 检查图像尺寸限制
            max_size = 4096
            if image.width > max_size or image.height > max_size:
                yield self.create_json_message({
                    "success": False,
                    "error": f"Image size too large. Maximum size is {max_size}x{max_size}",
                    "error_code": 413
                })
                return
            
            # 解析标注数据
            try:
                annotations_data = json.loads(annotations_str)
                
                # 支持两种格式：
                # 1. 包含annotations字段的对象: {"annotations": [...]}
                # 2. 直接的标注对象或数组: {...} 或 [...]
                if isinstance(annotations_data, dict) and 'annotations' in annotations_data:
                    # 格式1: {"annotations": [...]}
                    annotations = annotations_data['annotations']
                elif isinstance(annotations_data, list):
                    # 格式2: 直接的数组 [...]
                    annotations = annotations_data
                elif isinstance(annotations_data, dict):
                    # 格式3: 单个标注对象 {...}，转换为数组
                    annotations = [annotations_data]
                else:
                    yield self.create_json_message({
                        "success": False,
                        "error": "Invalid annotations format. Expected object or array",
                        "error_code": 422
                    })
                    return
                
                if not isinstance(annotations, list):
                    yield self.create_json_message({
                        "success": False,
                        "error": "annotations must be a list",
                        "error_code": 422
                    })
                    return
                    
                if len(annotations) > 100:
                    yield self.create_json_message({
                        "success": False,
                        "error": "Too many annotations. Maximum is 100",
                        "error_code": 422
                    })
                    return
                    
            except json.JSONDecodeError as e:
                yield self.create_json_message({
                    "success": False,
                    "error": f"Invalid JSON format in annotations: {str(e)}",
                    "error_code": 422
                })
                return
            
            # 验证标注数据格式
            valid_annotations = []
            for i, annotation in enumerate(annotations):
                if not isinstance(annotation, dict):
                    continue
                
                # 支持多种边界框字段名称
                bbox = None
                for bbox_field in ['bbox', 'bbox_2d', 'bounding_box', 'box']:
                    if bbox_field in annotation:
                        bbox = annotation[bbox_field]
                        break
                
                if bbox is None or not isinstance(bbox, list) or len(bbox) != 4:
                    continue
                    
                try:
                    bbox = [float(x) for x in bbox]
                    # 统一使用bbox字段名
                    annotation['bbox'] = bbox
                    valid_annotations.append(annotation)
                except (ValueError, TypeError):
                    continue
            
            if not valid_annotations and annotations:
                yield self.create_json_message({
                    "success": False,
                    "error": "No valid annotations found. Each annotation must have a 'bbox' field with 4 numbers",
                    "error_code": 422
                })
                return
            
            # 绘制标注
            annotated_image = self._draw_annotations(
                image, valid_annotations, box_color, text_color, line_width, font_size, coordinate_type
            )
            
            # 转换为二进制数据用于Dify显示
            img_byte_arr = BytesIO()
            annotated_image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # 使用blob消息返回图像（Dify标准方式）
            yield self.create_blob_message(
                blob=img_byte_arr,
                meta={"mime_type": "image/png"}
            )
            
            # 返回处理结果信息
            yield self.create_json_message({
                "success": True,
                "annotation_count": len(valid_annotations),
                "total_annotations": len(annotations),
                "image_size": {"width": annotated_image.width, "height": annotated_image.height},
                "message": f"成功绘制{len(valid_annotations)}个标注"
            })
            
        except requests.exceptions.RequestException as e:
            yield self.create_json_message({
                "success": False,
                "error": f"Network error when loading image: {str(e)}",
                "error_code": 404
            })
        except ValueError as e:
            yield self.create_json_message({
                "success": False,
                "error": f"Invalid parameter value: {str(e)}",
                "error_code": 400
            })
        except MemoryError:
            yield self.create_json_message({
                "success": False,
                "error": "Image too large to process",
                "error_code": 413
            })
        except Exception as e:
            yield self.create_json_message({
                "success": False,
                "error": f"Processing failed: {str(e)}",
                "error_code": 500
            })
    
    def _is_valid_color(self, color: str) -> bool:
        """验证颜色格式"""
        if not isinstance(color, str):
            return False
        if not color.startswith('#'):
            return False
        if len(color) != 7:
            return False
        try:
            int(color[1:], 16)
            return True
        except ValueError:
            return False
    
    def _load_image(self, image_data) -> Image.Image:
        """加载图像数据"""
        try:
            # 检查是否为Dify文件对象格式
            if isinstance(image_data, dict) and "#files#" in image_data:
                # Dify文件对象格式
                files = image_data.get("#files#", [])
                if files and len(files) > 0:
                    file_info = files[0]
                    # 优先使用url，如果没有则使用remote_url
                    image_url = file_info.get("url") or file_info.get("remote_url")
                    if image_url:
                        # 检查是否为base64格式
                        if image_url.startswith('data:image'):
                            # Base64格式（带前缀）
                            base64_data = image_url.split(',')[1]
                            image_bytes = base64.b64decode(base64_data)
                            return Image.open(BytesIO(image_bytes)).convert('RGB')
                        elif image_url.startswith('http'):
                            # HTTP URL格式
                            response = requests.get(image_url, timeout=30)
                            response.raise_for_status()
                            return Image.open(BytesIO(response.content)).convert('RGB')
                        else:
                            # 尝试作为纯base64处理
                            try:
                                image_bytes = base64.b64decode(image_url)
                                return Image.open(BytesIO(image_bytes)).convert('RGB')
                            except:
                                pass
                return None
            elif isinstance(image_data, str):
                # 清理字符串：去除前后空格和反引号
                cleaned_data = image_data.strip().strip('`').strip()
                
                try:
                    # 尝试解析为JSON（可能是Dify文件对象的字符串格式）
                    parsed_data = json.loads(cleaned_data)
                    if isinstance(parsed_data, dict) and "#files#" in parsed_data:
                        return self._load_image(parsed_data)
                except (json.JSONDecodeError, ValueError):
                    pass
                
                # 原有的处理逻辑
                if cleaned_data.startswith('http'):
                    # URL格式
                    try:
                        response = requests.get(cleaned_data, timeout=30)
                        response.raise_for_status()
                        
                        # 检查响应状态码
                        if response.status_code == 429:
                            print(f"Debug: Rate limited (429) for URL: {cleaned_data}")
                            return None
                        elif response.status_code != 200:
                            print(f"Debug: HTTP error {response.status_code} for URL: {cleaned_data}")
                            return None
                            
                        # 检查内容类型
                        content_type = response.headers.get('content-type', '').lower()
                        if not content_type.startswith('image/'):
                            print(f"Debug: Invalid content type '{content_type}' for URL: {cleaned_data}")
                            return None
                            
                        # 检查内容长度
                        if len(response.content) == 0:
                            print(f"Debug: Empty response content for URL: {cleaned_data}")
                            return None
                            
                        return Image.open(BytesIO(response.content)).convert('RGB')
                    except requests.exceptions.RequestException as e:
                        print(f"Debug: Request failed for URL {cleaned_data}: {e}")
                        return None
                elif cleaned_data.startswith('data:image'):
                    # Base64格式（带前缀）
                    base64_data = cleaned_data.split(',')[1]
                    image_bytes = base64.b64decode(base64_data)
                    return Image.open(BytesIO(image_bytes)).convert('RGB')
                else:
                    # 纯Base64格式
                    image_bytes = base64.b64decode(cleaned_data)
                    return Image.open(BytesIO(image_bytes)).convert('RGB')
            else:
                # 直接传递的字典对象（非字符串）
                if isinstance(image_data, dict):
                    return self._load_image(image_data)
        except Exception as e:
            print(f"Debug: _load_image exception: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _draw_annotations(self, image: Image.Image, annotations: list, 
                         box_color: str, text_color: str, line_width: int, font_size: int, coordinate_type: str = 'relative') -> Image.Image:
        """在图像上绘制标注"""
        # 创建图像副本
        annotated_image = image.copy()
        draw = ImageDraw.Draw(annotated_image)
        
        # 计算基于图像尺寸的缩放因子（使用更温和的缩放算法）
        # 确保缩放因子在 0.5-1.5 之间，避免过度缩放
        scale_factor = 0.5 + 0.5 * (min(image.width, image.height) / 1000.0)
        
        # 计算实际字体大小，并设置合理的最小值和最大值限制
        actual_font_size = int(font_size * scale_factor)
        actual_font_size = max(8, min(actual_font_size, 120))  # 最小8像素，最大120像素
        
        # 计算实际线框宽度，并设置合理的最小值和最大值限制
        actual_line_width = int(line_width * scale_factor)
        actual_line_width = max(1, min(actual_line_width, 50))  # 最小1像素，最大50像素
        
        # 添加调试信息，显示缩放计算过程
        print(f"Debug: Image size: {image.width}x{image.height}")
        print(f"Debug: Scale factor: {scale_factor:.2f}")
        print(f"Debug: Font size: {font_size} -> {actual_font_size} (scale: {scale_factor:.2f})")
        print(f"Debug: Line width: {line_width} -> {actual_line_width} (scale: {scale_factor:.2f})")
        
        # 尝试加载字体
        font = None
        font_loaded = False
        
        # 尝试多种字体路径
        font_paths = [
            "/System/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/Times.ttc",
            "/System/Library/Fonts/Courier.ttc"
        ]
        
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, actual_font_size)
                font_loaded = True
                break
            except (OSError, IOError):
                continue
        
        # 如果所有TrueType字体都加载失败，使用默认字体
        if not font_loaded:
            try:
                # 尝试使用PIL的默认字体，但设置大小
                font = ImageFont.load_default()
                # 注意：PIL的默认字体不支持大小设置，所以我们需要特殊处理
            except:
                font = ImageFont.load_default()
        
        for annotation in annotations:
            try:
                # 确保annotation是字典类型
                if not isinstance(annotation, dict):
                    continue
                    
                bbox = annotation.get('bbox', [])
                label = annotation.get('label', '')
                confidence = annotation.get('confidence', 1.0)
                
                if len(bbox) != 4:
                    continue
                
                x1, y1, x2, y2 = bbox
                
                # 根据坐标类型进行转换
                if coordinate_type == 'relative':
                    # 将相对坐标(0-1000)转换为真实像素坐标
                    x1 = (x1 / 1000.0) * image.width
                    y1 = (y1 / 1000.0) * image.height
                    x2 = (x2 / 1000.0) * image.width
                    y2 = (y2 / 1000.0) * image.height
                # 如果是absolute类型，直接使用原始坐标
                
                # 确保坐标在图像范围内
                x1 = max(0, min(x1, image.width))
                y1 = max(0, min(y1, image.height))
                x2 = max(0, min(x2, image.width))
                y2 = max(0, min(y2, image.height))
                
                # 绘制边界框
                draw.rectangle([x1, y1, x2, y2], outline=box_color, width=actual_line_width)
                
                # 绘制标签文本
                if label:
                    text = f"{label}"
                    if confidence < 1.0:
                        text += f" ({confidence:.2f})"
                    
                    # 计算文本位置，使用缩放后的字体大小和间距
                    text_spacing = max(2, int(5 * scale_factor))  # 确保最小间距
                    
                    # 获取文本边界框来计算准确的文本高度
                    try:
                        text_bbox = draw.textbbox((0, 0), text, font=font)
                        text_height = text_bbox[3] - text_bbox[1]
                        text_width = text_bbox[2] - text_bbox[0]
                    except:
                        # 如果textbbox不可用，使用估算值
                        text_height = actual_font_size if font_loaded else int(actual_font_size * 0.8)
                        text_width = len(text) * (actual_font_size // 2) if font_loaded else len(text) * int(actual_font_size * 0.4)
                    
                    # 计算文本Y位置，确保不会超出图像边界
                    text_y = y1 - text_height - text_spacing
                    if text_y < 0:
                        # 如果文本会超出上边界，放在边界框内部
                        text_y = y1 + text_spacing
                    
                    # 计算文本X位置，确保不会超出图像边界
                    text_x = x1
                    if text_x + text_width > image.width:
                        text_x = max(0, image.width - text_width)
                    
                    # 绘制文本背景
                    try:
                        # 使用实际的文本边界框
                        bbox_text = draw.textbbox((text_x, text_y), text, font=font)
                        # 添加一些内边距
                        padding = max(1, int(2 * scale_factor))
                        bg_bbox = [
                            bbox_text[0] - padding,
                            bbox_text[1] - padding,
                            bbox_text[2] + padding,
                            bbox_text[3] + padding
                        ]
                        draw.rectangle(bg_bbox, fill=box_color)
                    except:
                        # 如果textbbox不可用，使用估算的背景
                        padding = max(1, int(2 * scale_factor))
                        bg_bbox = [
                            text_x - padding,
                            text_y - padding,
                            text_x + text_width + padding,
                            text_y + text_height + padding
                        ]
                        draw.rectangle(bg_bbox, fill=box_color)
                    
                    # 绘制文本
                    draw.text((text_x, text_y), text, fill=text_color, font=font)
                    
            except Exception as e:
                # 跳过有问题的标注，但记录错误信息用于调试
                print(f"Debug: Error processing annotation {annotation}: {e}")
                continue
        
        return annotated_image
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """将图像转换为Base64格式"""
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()
        base64_string = base64.b64encode(image_bytes).decode('utf-8')
        return f"data:image/png;base64,{base64_string}"
