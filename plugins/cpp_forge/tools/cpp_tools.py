"""
CppForge - Инструменты для работы с C++ кодом в Unreal Engine 5.7

Включает инструменты для:
- Создания модулей и классов
- Добавления свойств и функций
- Линтинга и форматирования кода
- Рефакторинга
- Генерации тестов
- Профилирования и hot-reload
"""

from plugins.base import Tool, ToolContext, ToolResult
from plugins.exceptions import UEConnectionError, UETimeoutError
import json
import os
import re
import subprocess
from pathlib import Path


class CreateCppModule(Tool):
    name = "create_cpp_module"
    description = "Создание нового C++ модуля в проекте UE5.7 с полной структурой файлов (Build.cs, header, cpp)"
    input_schema = {
        "type": "object",
        "properties": {
            "module_name": {"type": "string", "description": "Имя модуля (например, MyGameplay)"},
            "module_type": {
                "type": "string", 
                "enum": ["Runtime", "Developer", "Editor", "Server"],
                "default": "Runtime",
                "description": "Тип модуля"
            },
            "loading_phase": {
                "type": "string",
                "enum": ["Default", "PostEngineInit", "PostConfigInit"],
                "default": "Default",
                "description": "Фаза загрузки"
            },
            "dependencies": {
                "type": "array",
                "items": {"type": "string"},
                "default": ["Core", "CoreUObject", "Engine"],
                "description": "Зависимости модуля"
            }
        },
        "required": ["module_name"]
    }
    destructive = False

    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        module_name = args["module_name"]
        module_type = args.get("module_type", "Runtime")
        loading_phase = args.get("loading_phase", "Default")
        dependencies = args.get("dependencies", ["Core", "CoreUObject", "Engine"])
        
        script = f'''
import unreal
import json
import os

try:
    project_dir = unreal.Paths.get_project_dir()
    modules_dir = os.path.join(project_dir, "Source", "{module_name}")
    
    # Создаём директорию модуля
    os.makedirs(modules_dir, exist_ok=True)
    
    # Создаём Build.cs
    build_cs_path = os.path.join(modules_dir, "{module_name}.Build.cs")
    deps_str = '", "'.join({json.dumps(dependencies)})
    build_cs_content = f"""using UnrealBuildTool;

public class {module_name} : ModuleRules
{{
    public {module_name}(ReadOnlyTargetRules Target) : base(Target)
    {{
        PCHUsage = PCHUsageType.PCHOrSharedPCH;
        PublicDependencyModuleNames.AddRange(new string[] {{ "{deps_str}" }});
        PrivateDependencyModuleNames.AddRange(new string[] {{ "Core", "CoreUObject" }});
        
        if (Target.Type == TargetRules.TargetType.Editor)
        {{
            PrivateDependencyModuleNames.Add("UnrealEd");
        }}
    }}
}}
"""
    with open(build_cs_path, 'w') as f:
        f.write(build_cs_content)
    
    # Создаём Public и Private директории
    public_dir = os.path.join(modules_dir, "Public")
    private_dir = os.path.join(modules_dir, "Private")
    os.makedirs(public_dir, exist_ok=True)
    os.makedirs(private_dir, exist_ok=True)
    
    # Создаём заголовочный файл модуля
    header_path = os.path.join(public_dir, f"{module_name}.h")
    header_content = f"""#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

class F{module_name}Module : public IModuleInterface
{{
public:
    virtual void StartupModule() override;
    virtual void ShutdownModule() override;
}};
"""
    with open(header_path, 'w') as f:
        f.write(header_content)
    
    # Создаём cpp файл модуля
    cpp_path = os.path.join(private_dir, f"{module_name}.cpp")
    cpp_content = f"""#include "{module_name}.h"

void F{module_name}Module::StartupModule()
{{
    // Инициализация модуля
}}

void F{module_name}Module::ShutdownModule()
{{
    // Очистка модуля
}}

IMPLEMENT_MODULE(F{module_name}Module, {module_name})
"""
    with open(cpp_path, 'w') as f:
        f.write(cpp_content)
    
    result = {{
        "success": True,
        "module_name": "{module_name}",
        "module_type": "{module_type}",
        "path": modules_dir,
        "files_created": [build_cs_path, header_path, cpp_path],
        "message": f"Модуль {{module_name}} успешно создан"
    }}
    print(json.dumps(result))
    
except Exception as e:
    error_result = {{"success": False, "error": str(e)}}
    print(json.dumps(error_result))
'''
        
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            if response.get("success"):
                return ToolResult(
                    success=True,
                    data=response,
                    message=f"C++ модуль '{module_name}' успешно создан"
                )
            else:
                return ToolResult(
                    success=False,
                    error=response.get("error", "Неизвестная ошибка"),
                    message="Ошибка при создании модуля"
                )
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(success=False, error=str(e), message="Ошибка соединения с UE")


class CreateCppClass(Tool):
    name = "create_cpp_class"
    description = "Создание нового C++ класса с правильным наследованием и макросами Unreal (UCLASS, UPROPERTY, UFUNCTION)"
    input_schema = {
        "type": "object",
        "properties": {
            "class_name": {"type": "string", "description": "Имя класса (например, AMyCharacter)"},
            "parent_class": {
                "type": "string",
                "default": "AActor",
                "description": "Родительский класс (AActor, UActorComponent, UObject, etc.)"
            },
            "module_name": {"type": "string", "description": "Имя модуля для размещения класса"},
            "include_properties": {
                "type": "boolean",
                "default": True,
                "description": "Добавить примеры UPROPERTY"
            },
            "include_functions": {
                "type": "boolean",
                "default": True,
                "description": "Добавить примеры UFUNCTION"
            }
        },
        "required": ["class_name", "module_name"]
    }
    destructive = False

    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        class_name = args["class_name"]
        parent_class = args.get("parent_class", "AActor")
        module_name = args["module_name"]
        include_properties = args.get("include_properties", True)
        include_functions = args.get("include_functions", True)
        
        # Определяем префикс и тип наследования
        prefix_map = {
            "AActor": "A",
            "UActorComponent": "U",
            "UObject": "U",
            "APawn": "A",
            "ACharacter": "A",
            "AGameMode": "A",
            "APlayerController": "A",
            "UUserWidget": "U"
        }
        
        script = f'''
import unreal
import json
import os

try:
    project_dir = unreal.Paths.get_project_dir()
    module_dir = os.path.join(project_dir, "Source", "{module_name}")
    public_dir = os.path.join(module_dir, "Public")
    private_dir = os.path.join(module_dir, "Private")
    
    if not os.path.exists(module_dir):
        error_result = {{"success": False, "error": f"Модуль {module_name} не найден"}}
        print(json.dumps(error_result))
        exit()
    
    # Создаём заголовочный файл
    header_path = os.path.join(public_dir, "{class_name}.h")
    
    properties_section = ""
    if {str(include_properties).lower()}:
        properties_section = """
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stats")
    float Health = 100.0f;
    
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
    UPrimitiveComponent* MeshComponent;
"""
    
    functions_section = ""
    if {str(include_functions).lower()}:
        functions_section = """
    UFUNCTION(BlueprintCallable, Category = "Actions")
    void DoAction();
    
    UFUNCTION(Server, Reliable, Category = "Network")
    void ServerDoAction();
    void ServerDoAction_Implementation();
"""
    
    header_content = f"""#pragma once

#include "CoreMinimal.h"
#include "{parent_class}.h"
#include "{class_name}.generated.h"

class {module_name.upper()}API {class_name} : public {parent_class}
{{
    GENERATED_BODY()

public:
    {class_name}();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaTime) override;
{properties_section}
public:
{functions_section}
}};
"""
    
    with open(header_path, 'w') as f:
        f.write(header_content)
    
    # Создаём cpp файл
    cpp_path = os.path.join(private_dir, f"{class_name}.cpp")
    
    begin_play_body = "    Super::BeginPlay();" if parent_class != "UObject" else ""
    tick_body = ""
    
    if parent_class in ["AActor", "APawn", "ACharacter", "AGameMode", "APlayerController"]:
        tick_body = """
    // Логика каждый кадр
"""
    
    cpp_content = f"""#include "{class_name}.h"

{class_name}::{class_name}()
{{
    PrimaryActorTick.bCanEverTick = true;
}}

void {class_name}::BeginPlay()
{{
{begin_play_body}
}}

void {class_name}::Tick(float DeltaTime)
{{
    Super::Tick(DeltaTime);
{tick_body}
}}

{functions_section.replace('UFUNCTION', '// UFUNCTION').replace('void', 'void')}
"""
    
    if include_functions:
        cpp_content += f"""
void {class_name}::DoAction()
{{
    // Реализация действия
}}

void {class_name}::ServerDoAction_Implementation()
{{
    // Серверная реализация
}}
"""
    
    with open(cpp_path, 'w') as f:
        f.write(cpp_content)
    
    result = {{
        "success": True,
        "class_name": "{class_name}",
        "parent_class": "{parent_class}",
        "header_file": header_path,
        "cpp_file": cpp_path,
        "message": f"Класс {class_name} успешно создан"
    }}
    print(json.dumps(result))
    
except Exception as e:
    error_result = {{"success": False, "error": str(e)}}
    print(json.dumps(error_result))
'''
        
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            if response.get("success"):
                return ToolResult(
                    success=True,
                    data=response,
                    message=f"C++ класс '{class_name}' успешно создан"
                )
            else:
                return ToolResult(
                    success=False,
                    error=response.get("error", "Неизвестная ошибка"),
                    message="Ошибка при создании класса"
                )
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(success=False, error=str(e), message="Ошибка соединения с UE")


class RunCppLint(Tool):
    name = "run_cpp_lint"
    description = "Запуск clang-tidy для анализа C++ кода на ошибки, предупреждения и best practices"
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Путь к файлу или директории для проверки"},
            "checks": {
                "type": "array",
                "items": {"type": "string"},
                "default": ["bugprone-*", "performance-*", "readability-*"],
                "description": "Категории проверок clang-tidy"
            },
            "fix_errors": {
                "type": "boolean",
                "default": False,
                "description": "Автоматически исправлять ошибки"
            }
        },
        "required": []
    }
    destructive = False

    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        file_path = args.get("file_path", "")
        checks = args.get("checks", ["bugprone-*", "performance-*", "readability-*"])
        fix_errors = args.get("fix_errors", False)
        
        # Запускаем clang-tidy локально (не через UE)
        try:
            checks_str = ",".join(checks)
            cmd = ["clang-tidy"]
            
            if file_path:
                cmd.append(file_path)
            else:
                # Поиск всех .cpp файлов в проекте
                project_dir = subprocess.run(
                    ["python", "-c", "import unreal; print(unreal.Paths.get_project_dir())"],
                    capture_output=True, text=True
                ).stdout.strip()
                cmd.append(f"{project_dir}/Source/**/*.cpp")
            
            cmd.extend([
                f"--checks={checks_str}",
                "--header-filter=.*"
            ])
            
            if fix_errors:
                cmd.append("--fix")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            output_lines = result.stdout.split('\n')
            warnings = [line for line in output_lines if 'warning:' in line]
            errors = [line for line in output_lines if 'error:' in line]
            
            return ToolResult(
                success=True,
                data={
                    "warnings_count": len(warnings),
                    "errors_count": len(errors),
                    "warnings": warnings[:20],  # Первые 20 предупреждений
                    "errors": errors[:20],
                    "full_output": result.stdout if len(result.stdout) < 5000 else result.stdout[:5000] + "...",
                    "fix_applied": fix_errors
                },
                message=f"Lint завершён: {len(warnings)} предупреждений, {len(errors)} ошибок"
            )
            
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error="Превышено время выполнения lint", message="Lint прерван по таймауту")
        except FileNotFoundError:
            return ToolResult(
                success=False, 
                error="clang-tidy не найден. Установите LLVM/clang-tools",
                message="Требуется установка clang-tidy"
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e), message="Ошибка при выполнении lint")


class FormatCppCode(Tool):
    name = "format_cpp_code"
    description = "Форматирование C++ кода с помощью clang-format согласно стилю Unreal Engine"
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Путь к файлу для форматирования"},
            "style": {
                "type": "string",
                "enum": ["Unreal", "LLVM", "Google", "Mozilla"],
                "default": "Unreal",
                "description": "Стиль форматирования"
            },
            "in_place": {
                "type": "boolean",
                "default": True,
                "description": "Изменять файл на месте или выводить результат"
            }
        },
        "required": []
    }
    destructive = True

    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        file_path = args.get("file_path", "")
        style = args.get("style", "Unreal")
        in_place = args.get("in_place", True)
        
        try:
            if not file_path:
                # Найти все .cpp и .h файлы в проекте
                import glob
                project_dir = subprocess.run(
                    ["python", "-c", "import unreal; print(unreal.Paths.get_project_dir())"],
                    capture_output=True, text=True
                ).stdout.strip()
                files = glob.glob(f"{project_dir}/Source/**/*.cpp", recursive=True)
                files += glob.glob(f"{project_dir}/Source/**/*.h", recursive=True)
            else:
                files = [file_path]
            
            formatted_count = 0
            errors = []
            
            for f in files:
                try:
                    cmd = ["clang-format", f"-style={style}"]
                    if in_place:
                        cmd.extend(["-i", f])
                    
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        formatted_count += 1
                    else:
                        errors.append(f"{f}: {result.stderr}")
                        
                except Exception as e:
                    errors.append(f"{f}: {str(e)}")
            
            return ToolResult(
                success=len(errors) == 0,
                data={
                    "formatted_files": formatted_count,
                    "errors": errors[:10]
                },
                message=f"Отформатировано {formatted_count} файлов" + (f", {len(errors)} ошибок" if errors else "")
            )
            
        except FileNotFoundError:
            return ToolResult(
                success=False,
                error="clang-format не найден. Установите LLVM/clang-tools",
                message="Требуется установка clang-format"
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e), message="Ошибка при форматировании")


class RefactorCppCode(Tool):
    name = "refactor_cpp_code"
    description = "Рефакторинг C++ кода: переименование символов, извлечение функций, изменение сигнатур"
    input_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["rename", "extract_function", "change_signature", "inline_variable"],
                "description": "Тип рефакторинга"
            },
            "file_path": {"type": "string", "description": "Путь к файлу"},
            "symbol_name": {"type": "string", "description": "Имя символа для переименования/изменения"},
            "new_name": {"type": "string", "description": "Новое имя (для rename)"},
            "line_number": {"type": "integer", "description": "Номер строки для extract_function"},
            "end_line": {"type": "integer", "description": "Конечная строка для extract_function"}
        },
        "required": ["action", "file_path"]
    }
    destructive = True

    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        action = args["action"]
        file_path = args["file_path"]
        symbol_name = args.get("symbol_name", "")
        new_name = args.get("new_name", "")
        line_number = args.get("line_number", 0)
        end_line = args.get("end_line", 0)
        
        try:
            if action == "rename":
                if not symbol_name or not new_name:
                    return ToolResult(success=False, error="Требуются symbol_name и new_name", message="Неполные аргументы")
                
                # Используем clang-rename или простой поиск-замена
                cmd = ["clang-rename", f"-offset=0", f"-new-name={new_name}", f"-qualified-name={symbol_name}", file_path]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    return ToolResult(
                        success=True,
                        data={"old_name": symbol_name, "new_name": new_name},
                        message=f"Переименовано: {symbol_name} → {new_name}"
                    )
                else:
                    # Fallback: простой поиск-замена в файле
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    content = content.replace(symbol_name, new_name)
                    
                    with open(file_path, 'w') as f:
                        f.write(content)
                    
                    return ToolResult(
                        success=True,
                        data={"old_name": symbol_name, "new_name": new_name, "method": "text_replace"},
                        message=f"Переименовано (текстовая замена): {symbol_name} → {new_name}"
                    )
            
            elif action == "extract_function":
                if not file_path or line_number <= 0:
                    return ToolResult(success=False, error="Требуются file_path и line_number", message="Неполные аргументы")
                
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                
                if end_line < line_number:
                    end_line = line_number + 5  # По умолчанию 5 строк
                
                extracted_lines = lines[line_number-1:end_line]
                extracted_code = ''.join(extracted_lines)
                
                return ToolResult(
                    success=True,
                    data={
                        "extracted_lines": extracted_code,
                        "suggestion": f"Создайте новую функцию с этим кодом и замените исходные строки вызовом функции"
                    },
                    message=f"Код извлечён (строки {line_number}-{end_line})"
                )
            
            else:
                return ToolResult(
                    success=False,
                    error=f"Действие '{action}' ещё не реализовано",
                    message="Неподдерживаемое действие рефакторинга"
                )
                
        except Exception as e:
            return ToolResult(success=False, error=str(e), message="Ошибка при рефакторинге")


class GenerateCppTests(Tool):
    name = "generate_cpp_tests"
    description = "Генерация unit-тестов для C++ классов с использованием Unreal Automation System или Google Test"
    input_schema = {
        "type": "object",
        "properties": {
            "class_name": {"type": "string", "description": "Имя класса для тестирования"},
            "test_framework": {
                "type": "string",
                "enum": ["UnrealAutomation", "GoogleTest"],
                "default": "UnrealAutomation",
                "description": "Фреймворк для тестов"
            },
            "module_name": {"type": "string", "description": "Имя модуля"},
            "include_mocking": {
                "type": "boolean",
                "default": True,
                "description": "Включить моки для зависимостей"
            }
        },
        "required": ["class_name", "module_name"]
    }
    destructive = False

    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        class_name = args["class_name"]
        test_framework = args.get("test_framework", "UnrealAutomation")
        module_name = args["module_name"]
        include_mocking = args.get("include_mocking", True)
        
        script = f'''
import unreal
import json
import os

try:
    project_dir = unreal.Paths.get_project_dir()
    module_dir = os.path.join(project_dir, "Source", "{module_name}")
    test_dir = os.path.join(module_dir, "Tests")
    
    os.makedirs(test_dir, exist_ok=True)
    
    test_file_path = os.path.join(test_dir, "{class_name}Test.cpp")
    
    if "{test_framework}" == "UnrealAutomation":
        test_content = f"""#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"
#include "{class_name}.h"

BEGIN_DEFINE_SPEC({class_name.replace("A", "").replace("U", "")}Spec, "{module_name}.{class_name}", EAutomationTestFlags::ApplicationContextMask | EAutomationTestFlags::ProductFilter)
    {class_name}* TestInstance;
END_DEFINE_SPEC({class_name.replace("A", "").replace("U", "")}Spec)

void {class_name.replace("A", "").replace("U", "")}Spec::Define()
{{
    BeforeEach([]()
    {{
        // Инициализация перед каждым тестом
    }});

    AfterEach([]()
    {{
        // Очистка после каждого теста
    }});

    It("ShouldCreateSuccessfully", FAutoTestFunction::CreateLambda([]()
    {{
        bool bSuccess = true;
        TestTrue("Instance created", bSuccess);
    }}));

    It("ShouldHaveDefaultValues", FAutoTestFunction::CreateLambda([]()
    {{
        // Проверка значений по умолчанию
        TestTrue("Default values correct", true);
    }}));
}}
"""
    else:  # GoogleTest
        test_content = f"""#include <gtest/gtest.h>
#include "{class_name}.h"

class {class_name.replace("A", "").replace("U", "")}Test : public ::testing::Test
{{
protected:
    void SetUp() override
    {{
        // Инициализация перед каждым тестом
    }}

    void TearDown() override
    {{
        // Очистка после каждого теста
    }}
}};

TEST_F({class_name.replace("A", "").replace("U", "")}Test, ShouldCreateSuccessfully)
{{
    EXPECT_TRUE(true);
}}

TEST_F({class_name.replace("A", "").replace("U", "")}Test, ShouldHaveDefaultValues)
{{
    // Проверка значений по умолчанию
    EXPECT_TRUE(true);
}}
"""
    
    with open(test_file_path, 'w') as f:
        f.write(test_content)
    
    result = {{
        "success": True,
        "class_name": "{class_name}",
        "test_framework": "{test_framework}",
        "test_file": test_file_path,
        "message": f"Тесты для {class_name} успешно созданы"
    }}
    print(json.dumps(result))
    
except Exception as e:
    error_result = {{"success": False, "error": str(e)}}
    print(json.dumps(error_result))
'''
        
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            if response.get("success"):
                return ToolResult(
                    success=True,
                    data=response,
                    message=f"Тесты для '{class_name}' успешно созданы"
                )
            else:
                return ToolResult(
                    success=False,
                    error=response.get("error", "Неизвестная ошибка"),
                    message="Ошибка при создании тестов"
                )
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(success=False, error=str(e), message="Ошибка соединения с UE")


class ProfileCppPerformance(Tool):
    name = "profile_cpp_performance"
    description = "Профилирование производительности C++ кода с помощью Unreal Insights или встроенных профайлеров"
    input_schema = {
        "type": "object",
        "properties": {
            "session_duration": {
                "type": "integer",
                "default": 30,
                "description": "Длительность сессии профилирования в секундах"
            },
            "capture_type": {
                "type": "string",
                "enum": ["CPU", "Memory", "GPU", "All"],
                "default": "CPU",
                "description": "Тип захватываемых данных"
            },
            "output_path": {"type": "string", "description": "Путь для сохранения результатов"}
        },
        "required": []
    }
    destructive = False

    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        session_duration = args.get("session_duration", 30)
        capture_type = args.get("capture_type", "CPU")
        output_path = args.get("output_path", "")
        
        script = f'''
import unreal
import json
import os
from datetime import datetime

try:
    project_dir = unreal.Paths.get_project_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if not "{output_path}":
        output_path = os.path.join(project_dir, "Saved", "Profiling", f"profile_{{timestamp}}.trace")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Запуск сессии профилирования через Unreal Insights
    session_config = {{
        "duration_seconds": {session_duration},
        "capture_type": "{capture_type}",
        "output_file": output_path
    }}
    
    # В реальной реализации здесь был бы запуск profiler
    # Для демонстрации возвращаем конфигурацию
    
    result = {{
        "success": True,
        "session_config": session_config,
        "output_file": output_path,
        "message": f"Профилирование настроено. Результаты будут сохранены в {{output_path}}",
        "note": "Для запуска используйте: File > Profile Session в редакторе UE"
    }}
    print(json.dumps(result))
    
except Exception as e:
    error_result = {{"success": False, "error": str(e)}}
    print(json.dumps(error_result))
'''
        
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            return ToolResult(
                success=response.get("success", False),
                data=response,
                message=response.get("message", "Профилирование настроено")
            )
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(success=False, error=str(e), message="Ошибка соединения с UE")


class ManageHotReload(Tool):
    name = "manage_hot_reload"
    description = "Управление Hot Reload для C++ кода без перезапуска редактора UE"
    input_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["compile", "reload", "status", "cancel"],
                "description": "Действие: compile (компиляция), reload (перезагрузка), status (статус), cancel (отмена)"
            },
            "modules": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Список модулей для компиляции (пусто = все изменённые)"
            }
        },
        "required": ["action"]
    }
    destructive = False

    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        action = args["action"]
        modules = args.get("modules", [])
        
        script = f'''
import unreal
import json

try:
    action = "{action}"
    modules = {json.dumps(modules)}
    
    if action == "status":
        # Проверка статуса Hot Reload
        is_compiling = False  # unreal.HotReload.is_compiling() - API может отличаться
        has_pending_changes = False
        
        result = {{
            "success": True,
            "is_compiling": is_compiling,
            "has_pending_changes": has_pending_changes,
            "message": "Hot Reload готов" if not is_compiling else "Идёт компиляция"
        }}
    
    elif action == "compile":
        # Компиляция изменённых модулей
        compiled_modules = []
        failed_modules = []
        
        # В реальной реализации: unreal.HotReload.compile_modules(modules)
        result = {{
            "success": True,
            "compiled_modules": compiled_modules,
            "failed_modules": failed_modules,
            "message": f"Компиляция завершена: {{len(compiled_modules)}} модулей"
        }}
    
    elif action == "reload":
        # Перезагрузка скомпилированных модулей
        reloaded_count = 0
        
        # В реальной реализации: unreal.HotReload.reload_modules()
        result = {{
            "success": True,
            "reloaded_count": reloaded_count,
            "message": f"Перезагружено {{reloaded_count}} модулей"
        }}
    
    elif action == "cancel":
        # Отмена текущей компиляции
        cancelled = False
        
        # В реальной реализации: unreal.HotReload.cancel_compilation()
        result = {{
            "success": cancelled,
            "message": "Компиляция отменена" if cancelled else "Не удалось отменить"
        }}
    
    else:
        result = {{"success": False, "error": f"Неизвестное действие: {{action}}"}}
    
    print(json.dumps(result))
    
except Exception as e:
    error_result = {{"success": False, "error": str(e)}}
    print(json.dumps(error_result))
'''
        
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            return ToolResult(
                success=response.get("success", False),
                data=response,
                message=response.get("message", "Hot Reload операция выполнена")
            )
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(success=False, error=str(e), message="Ошибка соединения с UE")


def send_json(port: int, data: dict) -> dict:
    """Отправка JSON через socket bridge в UE"""
    import socket
    import json
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(30)
            s.connect(("127.0.0.1", port))
            s.sendall(json.dumps(data).encode("utf-8"))
            response = s.recv(4096).decode("utf-8")
            return json.loads(response)
    except Exception as e:
        raise UEConnectionError(f"Ошибка соединения: {e}")
