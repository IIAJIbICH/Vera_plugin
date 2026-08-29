# CppForge Plugin - Инструменты для работы с C++ в UE5.7

## Обзор
Плагин **CppForge** предоставляет инструменты для генерации и управления C++ кодом в Unreal Engine 5.7.

## Доступные инструменты

### 1. `create_cpp_module`
**Описание:** Создание нового C++ модуля с базовой структурой файлов.

**Параметры:**
- `module_name` (string, required): Имя модуля
- `module_type` (string, optional): Тип модуля (Runtime/Developer/Editor)
- `loading_phase` (string, optional): Фаза загрузки (Default/PreLoading/PostLoading)

**Создаваемые файлы:**
- `{ModuleName}.Build.cs`
- `Public/{ModuleName}.h`
- `Private/{ModuleName}.cpp`

---

### 2. `create_cpp_class`
**Описание:** Создание C++ класса с указанным родительским классом.

**Параметры:**
- `class_name` (string, required): Имя класса (AMyCharacter, UMyComponent)
- `parent_class` (string, required): Родительский класс (AActor, UObject, UActorComponent)
- `module_name` (string, required): Модуль для размещения
- `header_only` (bool, optional): Только заголовочный файл

**Автоматически добавляет:**
- Правильные #include директивы
- GENERATED_BODY() макрос
- Конструктор класса

---

### 3. `generate_build_cs`
**Описание:** Генерация или обновление .Build.cs файла с зависимостями.

**Параметры:**
- `module_name` (string, required): Имя модуля
- `public_dependency_module_names` (array): Публичные зависимости
- `private_dependency_module_names` (array): Приватные зависимости

---

### 4. `add_property_to_class`
**Описание:** Добавление UPROPERTY в существующий C++ класс.

**Параметры:**
- `class_path` (string, required): Путь к файлу .h
- `property_name` (string, required): Имя свойства
- `property_type` (string, required): Тип (int32, FString, UProperty*)
- `specifiers` (array): Спецификаторы (EditAnywhere, BlueprintReadWrite)
- `category` (string): Категория свойства

---

### 5. `add_function_to_class`
**Описание:** Добавление UFUNCTION в существующий C++ класс.

**Параметры:**
- `class_path` (string, required): Путь к файлу .h
- `function_name` (string, required): Имя функции
- `return_type` (string): Тип возвращаемого значения
- `parameters` (array): Параметры функции
- `implementation_in_cpp` (bool): Создать реализацию в .cpp

---

### 6. `setup_include_paths`
**Описание:** Настройка дополнительных путей включения для модуля.

**Параметры:**
- `module_name` (string, required): Имя модуля
- `include_paths` (array, required): Пути для включения

---

### 7. `generate_module_documentation`
**Описание:** Генерация Doxygen-совместимой документации.

**Параметры:**
- `module_name` (string, required): Имя модуля
- `output_format` (string): Формат (html/markdown/xml)
- `output_dir` (string): Директория вывода

---

## Пример использования

```json
{
  "tool": "cpp_forge.tools.create_cpp_module",
  "args": {
    "module_name": "MyGameCore",
    "module_type": "Runtime"
  }
}
```

```json
{
  "tool": "cpp_forge.tools.create_cpp_class",
  "args": {
    "class_name": "AMyCharacter",
    "parent_class": "ACharacter",
    "module_name": "MyGameCore"
  }
}
```

## Структура плагина

```
plugins/cpp_forge/
├── plugin.json          # Конфигурация плагина
├── SKILL.md            # Документация
└── tools/
    └── create_cpp_module.py  # Реализация инструментов
```

## Интеграция с другими плагинами

CppForge может использоваться совместно с:
- **DbConnector** - для сохранения данных C++ объектов
- **AiArchitect** - для проектирования архитектуры модулей
- **CicdMaster** - для автоматической сборки C++ проектов
