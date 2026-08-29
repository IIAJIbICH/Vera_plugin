"""
Computer Use - Управление компьютером через скриншоты и клики
Требует установленный pyautogui
"""

from ..base import Tool, ToolResult, ToolContext


def lazy_import_pyautogui():
    """Ленивый импорт pyautogui с обработкой ошибок"""
    try:
        import pyautogui
        return pyautogui, None
    except ImportError:
        return None, "pyautogui не установлен. Установите: pip install pyautogui"
    except Exception as e:
        return None, f"Ошибка импорта pyautogui: {e}"


class ScreenCaptureTool(Tool):
    """Скриншот всего экрана"""
    
    name = "screen_capture"
    description = "Делает скриншот всего экрана"
    destructive = False
    
    input_schema = {
        "type": "object",
        "properties": {}
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        pyautogui, error = lazy_import_pyautogui()
        
        if error:
            return ToolResult(
                success=False,
                error=error,
                message="Требуется установка pyautogui"
            )
        
        try:
            screenshot = pyautogui.screenshot()
            
            return ToolResult(
                success=True,
                data={
                    "width": screenshot.width,
                    "height": screenshot.height,
                    "format": "PNG"
                },
                message=f"Скриншот сделан: {screenshot.width}x{screenshot.height}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                message="Ошибка создания скриншота"
            )


class ScreenClickTool(Tool):
    """Клик по координатам"""
    
    name = "screen_click"
    description = "Клик по указанным координатам экрана"
    destructive = True
    
    input_schema = {
        "type": "object",
        "properties": {
            "x": {
                "type": "integer",
                "description": "Координата X"
            },
            "y": {
                "type": "integer",
                "description": "Координата Y"
            },
            "button": {
                "type": "string",
                "enum": ["left", "right", "middle"],
                "description": "Кнопка мыши",
                "default": "left"
            }
        },
        "required": ["x", "y"]
    }
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        x = args.get("x")
        y = args.get("y")
        button = args.get("button", "left")
        
        if x is None or y is None:
            return ToolResult(
                success=False,
                error="Не указаны координаты",
                message="Передайте параметры x и y"
            )
        
        pyautogui, error = lazy_import_pyautogui()
        
        if error:
            return ToolResult(
                success=False,
                error=error,
                message="Требуется установка pyautogui"
            )
        
        try:
            pyautogui.click(x=x, y=y, button=button)
            
            return ToolResult(
                success=True,
                data={
                    "x": x,
                    "y": y,
                    "button": button
                },
                message=f"Клик выполнен в ({x}, {y})"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                message="Ошибка выполнения клика"
            )
