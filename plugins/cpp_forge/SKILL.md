# CppForge Plugin

## Описание
Генерация C++ кода для Unreal Engine 5.7, создание модулей, классов и настройка билд-системы.

## Инструменты

### create_cpp_module
Создание нового C++ модуля с базовой структурой.

**Параметры:**
- `module_name` (string): Имя модуля
- `module_type` (string): Тип модуля (Runtime, Developer, Editor)
- `loading_phase` (string): Фаза загрузки (Default, PreLoading, PostLoading)

### create_cpp_class
Создание C++ класса с наследованием от UObject, AActor, UActorComponent и т.д.

**Параметры:**
- `class_name` (string): Имя класса
- `parent_class` (string): Родительский класс
- `module_name` (string): Модуль для размещения
- `header_only` (bool): Только заголовочный файл
- `include_macros` (list): Макросы для включения (UCLASS, UPROPERTY, UFUNCTION)

### generate_build_cs
Генерация или обновление .Build.cs файла с зависимостями.

**Параметры:**
- `module_name` (string): Имя модуля
- `dependencies` (list): Список зависимостей
- `private_dependency_module_names` (list): Приватные зависимости
- `public_dependency_module_names` (list): Публичные зависимости

### add_property_to_class
Добавление UPROPERTY в существующий C++ класс.

**Параметры:**
- `class_path` (string): Путь к классу
- `property_name` (string): Имя свойства
- `property_type` (string): Тип свойства
- `specifiers` (list): Спецификаторы (EditAnywhere, BlueprintReadWrite, etc.)

### add_function_to_class
Добавление UFUNCTION в существующий C++ класс.

**Параметры:**
- `class_path` (string): Путь к классу
- `function_name` (string): Имя функции
- `return_type` (string): Тип возвращаемого значения
- `parameters` (list): Параметры функции
- `specifiers` (list): Спецификаторы (BlueprintCallable, Server, Client, etc.)

### setup_include_paths
Настройка путей включения для модуля.

**Параметры:**
- `module_name` (string): Имя модуля
- `include_paths` (list): Пути для включения

### generate_module_documentation
Генерация Doxygen-совместимой документации для модуля.

**Параметры:**
- `module_name` (string): Имя модуля
- `output_format` (string): Формат вывода (html, markdown, xml)

## Примеры использования

```json
{
  "tool": "create_cpp_module",
  "args": {
    "module_name": "MyGameCore",
    "module_type": "Runtime",
    "loading_phase": "Default"
  }
}
```

```json
{
  "tool": "create_cpp_class",
  "args": {
    "class_name": "AMyCharacter",
    "parent_class": "ACharacter",
    "module_name": "MyGameCore",
    "include_macros": ["UCLASS", "UPROPERTY", "UFUNCTION"]
  }
}
```
