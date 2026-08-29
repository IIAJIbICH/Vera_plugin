"""
Исключения для плагинов VERA
"""


class VERAError(Exception):
    """Базовое исключение VERA"""
    pass


class UEConnectionError(VERAError):
    """Ошибка соединения с Unreal Editor"""
    pass


class UETimeoutError(VERAError):
    """Превышено время ожидания ответа от Unreal Editor"""
    pass


class ToolExecutionError(VERAError):
    """Ошибка выполнения инструмента"""
    pass


class ValidationError(VERAError):
    """Ошибка валидации входных данных"""
    pass
