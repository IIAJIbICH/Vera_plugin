"""
Базовые классы для всех инструментов VERA
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ToolContext:
    """Контекст выполнения инструмента"""
    project_path: str
    plugin_path: str
    bridge_port: int
    user_id: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class ToolResult:
    """Результат выполнения инструмента"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data or {},
            "message": self.message,
            "error": self.error
        }


class Tool:
    """Базовый класс для всех инструментов"""
    
    name: str = ""
    description: str = ""
    input_schema: Dict[str, Any] = {}
    destructive: bool = False
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        """Выполняет инструмент с заданными аргументами"""
        raise NotImplementedError("Подкласс должен реализовать метод execute")
    
    def validate_input(self, args: dict) -> tuple[bool, Optional[str]]:
        """Валидирует входные аргументы по схеме"""
        if not self.input_schema:
            return True, None
        
        # Простая валидация required полей
        required = self.input_schema.get("required", [])
        for field in required:
            if field not in args:
                return False, f"Требуется поле: {field}"
        
        return True, None
