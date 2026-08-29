# CppForge Plugin

Инструменты для работы с C++ кодом в Unreal Engine 5.7.

## Возможности

- Создание C++ модулей с полной структурой файлов
- Генерация C++ классов с макросами Unreal (UCLASS, UPROPERTY, UFUNCTION)
- Линтинг кода через clang-tidy
- Форматирование кода через clang-format (стиль Unreal)
- Рефакторинг: переименование, извлечение функций
- Генерация unit-тестов (Unreal Automation или Google Test)
- Профилирование производительности
- Управление Hot Reload

## Инструменты

### 1. create_cpp_module
Создание нового C++ модуля с Build.cs, заголовочным и cpp файлами.

**Параметры:**
- `module_name` (required): Имя модуля
- `module_type`: Runtime, Developer, Editor, Server
- `loading_phase`: Default, PostEngineInit, PostConfigInit
- `dependencies`: Список зависимостей

### 2. create_cpp_class
Генерация C++ класса с правильным наследованием.

**Параметры:**
- `class_name` (required): Имя класса
- `module_name` (required): Модуль для размещения
- `parent_class`: Родительский класс (AActor, UActorComponent, etc.)
- `include_properties`: Добавить примеры UPROPERTY
- `include_functions`: Добавить примеры UFUNCTION

### 3. run_cpp_lint
Запуск clang-tidy для анализа кода.

**Параметры:**
- `file_path`: Путь к файлу или директории
- `checks`: Категории проверок
- `fix_errors`: Автоматическое исправление

### 4. format_cpp_code
Форматирование кода через clang-format.

**Параметры:**
- `file_path`: Путь к файлу
- `style`: Unreal, LLVM, Google, Mozilla
- `in_place`: Изменять файл на месте

**destructive = True**

### 5. refactor_cpp_code
Рефакторинг кода: переименование, извлечение функций.

**Параметры:**
- `action` (required): rename, extract_function, change_signature, inline_variable
- `file_path` (required): Путь к файлу
- `symbol_name`: Имя символа
- `new_name`: Новое имя (для rename)
- `line_number`: Номер строки (для extract_function)
- `end_line`: Конечная строка

**destructive = True**

### 6. generate_cpp_tests
Генерация unit-тестов для классов.

**Параметры:**
- `class_name` (required): Имя класса
- `module_name` (required): Имя модуля
- `test_framework`: UnrealAutomation или GoogleTest
- `include_mocking`: Включить моки

### 7. profile_cpp_performance
Профилирование производительности C++ кода.

**Параметры:**
- `session_duration`: Длительность в секундах
- `capture_type`: CPU, Memory, GPU, All
- `output_path`: Путь для сохранения

### 8. manage_hot_reload
Управление Hot Reload без перезапуска редактора.

**Параметры:**
- `action` (required): compile, reload, status, cancel
- `modules`: Список модулей

## Требования

- Unreal Engine 5.7
- LLVM/clang-tools (для lint и format)
- Настроенный bridge для связи с редактором UE

## Примеры использования

```python
# Создать модуль
await vera.call("create_cpp_module", {
    "module_name": "MyGameplay",
    "dependencies": ["Core", "CoreUObject", "Engine", "InputCore"]
})

# Создать класс
await vera.call("create_cpp_class", {
    "class_name": "AMyCharacter",
    "module_name": "MyGameplay",
    "parent_class": "ACharacter",
    "include_properties": True,
    "include_functions": True
})

# Запустить линтинг
await vera.call("run_cpp_lint", {
    "file_path": "Source/MyGameplay/Private",
    "checks": ["bugprone-*", "performance-*"],
    "fix_errors": False
})

# Отформатировать код
await vera.call("format_cpp_code", {
    "style": "Unreal",
    "in_place": True
})

# Сгенерировать тесты
await vera.call("generate_cpp_tests", {
    "class_name": "AMyCharacter",
    "module_name": "MyGameplay",
    "test_framework": "UnrealAutomation"
})
```
