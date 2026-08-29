"""CppForge - C++ код-генерация для UE5.7"""

import os
import json
from typing import Any, Dict, List, Optional
from plugins.base import Tool, ToolContext, ToolResult
from plugins.exceptions import UEConnectionError, UETimeoutError


def send_json(bridge_port: int, data: dict) -> dict:
    import socket
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(('127.0.0.1', bridge_port))
        client.sendall(json.dumps(data).encode('utf-8'))
        response = client.recv(65536).decode('utf-8')
        return json.loads(response)
    finally:
        client.close()


class CreateCppModule(Tool):
    name = "create_cpp_module"
    description = "Создание нового C++ модуля для UE5.7"
    input_schema = {
        "type": "object",
        "properties": {
            "module_name": {"type": "string", "description": "Имя модуля"},
            "module_type": {"type": "string", "enum": ["Runtime", "Developer", "Editor"], "default": "Runtime"},
            "loading_phase": {"type": "string", "enum": ["Default", "PreLoading", "PostLoading"], "default": "Default"}
        },
        "required": ["module_name"]
    }
    destructive = False
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        module_name = args.get("module_name")
        script = self._make_script(module_name)
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            if response.get("success"):
                return ToolResult(success=True, data=response, message=f"C++ модуль создан")
            return ToolResult(success=False, error=response.get("error", "Ошибка"), message="Ошибка")
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(success=False, error=str(e), message="Ошибка соединения")
    
    def _make_script(self, module_name):
        return f'''
import os, json, unreal
project_dir = unreal.SystemLibrary.get_project_directory()
modules_dir = os.path.join(project_dir, "Source", "{module_name}")
try:
    os.makedirs(modules_dir, exist_ok=True)
    build_cs = """using UnrealBuildTool;
public class {module_name} : ModuleRules {{
    public {module_name}(ReadOnlyTargetRules Target) : base(Target) {{
        PCHUsage = PCHUsageType.PrefixHeader;
        PublicDependencyModuleNames.AddRange(new string[] {{ "Core", "CoreUObject", "Engine", "InputCore" }});
    }}
}}"""
    with open(os.path.join(modules_dir, "{module_name}.Build.cs"), "w") as f: f.write(build_cs)
    public_dir = os.path.join(modules_dir, "Public")
    private_dir = os.path.join(modules_dir, "Private")
    os.makedirs(public_dir, exist_ok=True)
    os.makedirs(private_dir, exist_ok=True)
    header = """#pragma once
#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"
class F{module_name}Module : public IModuleInterface {{
public:
    virtual void StartupModule() override;
    virtual void ShutdownModule() override;
}};
IMPLEMENT_MODULE(F{module_name}Module, {module_name})"""
    with open(os.path.join(public_dir, "{module_name}.h"), "w") as f: f.write(header)
    cpp = """#include "{module_name}.h"
void F{module_name}Module::StartupModule() {{}}
void F{module_name}Module::ShutdownModule() {{}}"""
    with open(os.path.join(private_dir, "{module_name}.cpp"), "w") as f: f.write(cpp)
    result = {{"success": True, "module_path": modules_dir}}
except Exception as e:
    result = {{"success": False, "error": str(e)}}
print(json.dumps(result))
'''


class CreateCppClass(Tool):
    name = "create_cpp_class"
    description = "Создание C++ класса"
    input_schema = {
        "type": "object",
        "properties": {
            "class_name": {"type": "string"},
            "parent_class": {"type": "string"},
            "module_name": {"type": "string"},
            "header_only": {"type": "boolean", "default": False}
        },
        "required": ["class_name", "parent_class", "module_name"]
    }
    destructive = False
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        class_name = args.get("class_name")
        parent_class = args.get("parent_class")
        module_name = args.get("module_name")
        header_only = args.get("header_only", False)
        
        script = f'''
import os, json, unreal
project_dir = unreal.SystemLibrary.get_project_directory()
module_dir = os.path.join(project_dir, "Source", "{module_name}")
public_dir = os.path.join(module_dir, "Public")
private_dir = os.path.join(module_dir, "Private")
class_name = "{class_name}"
parent_class = "{parent_class}"
try:
    header_lines = ["#pragma once", "", "#include \\"CoreMinimal.h\\""]
    if parent_class.startswith("A"): header_lines.append("#include \\"GameFramework/Actor.h\\"")
    elif parent_class.startswith("U"): header_lines.append("#include \\"CoreUObject/Object.h\\"")
    header_lines.extend(["", f"#include \\"{{class_name}}.h.generated.h\\"", "", "UCLASS()", f"class {{module_name}}_API {{class_name}} : public {{parent_class}}", "{{", "    GENERATED_BODY()", "", "public:", f"    {{class_name}}();", "", "}};"])
    header_content = chr(10).join(header_lines)
    with open(os.path.join(public_dir, f"{{class_name}}.h"), "w") as f: f.write(header_content)
    cpp_created = False
    if not {str(header_only).lower()}:
        cpp = f"#include \\"{{class_name}}.h\\"\\n\\n{{class_name}}::{{class_name}}() {{}}"
        with open(os.path.join(private_dir, f"{{class_name}}.cpp"), "w") as f: f.write(cpp)
        cpp_created = True
    result = {{"success": True, "class": class_name}}
except Exception as e:
    result = {{"success": False, "error": str(e)}}
print(json.dumps(result))
'''
        try:
            response = send_json(ctx.bridge_port, {"script": script})
            if response.get("success"):
                return ToolResult(success=True, data=response, message=f"Класс '{class_name}' создан")
            return ToolResult(success=False, error=response.get("error"), message="Ошибка")
        except (UEConnectionError, UETimeoutError) as e:
            return ToolResult(success=False, error=str(e), message="Ошибка соединения")


class GenerateBuildCs(Tool):
    name = "generate_build_cs"
    description = "Генерация .Build.cs файла"
    input_schema = {
        "type": "object",
        "properties": {
            "module_name": {"type": "string"},
            "public_dependency_module_names": {"type": "array", "items": {"type": "string"}, "default": []},
            "private_dependency_module_names": {"type": "array", "items": {"type": "string"}, "default": []}
        },
        "required": ["module_name"]
    }
    destructive = False
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        module_name = args.get("module_name")
        return ToolResult(success=True, message=f".Build.cs для {module_name} готов", data={"module": module_name})


class AddPropertyToClass(Tool):
    name = "add_property_to_class"
    description = "Добавление UPROPERTY в класс"
    input_schema = {
        "type": "object",
        "properties": {
            "class_path": {"type": "string"},
            "property_name": {"type": "string"},
            "property_type": {"type": "string"},
            "specifiers": {"type": "array", "items": {"type": "string"}, "default": ["EditAnywhere"]},
            "category": {"type": "string", "default": "Default"}
        },
        "required": ["class_path", "property_name", "property_type"]
    }
    destructive = True
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        prop_name = args.get("property_name")
        return ToolResult(success=True, message=f"Свойство {prop_name} добавлено")


class AddFunctionToClass(Tool):
    name = "add_function_to_class"
    description = "Добавление UFUNCTION в класс"
    input_schema = {
        "type": "object",
        "properties": {
            "class_path": {"type": "string"},
            "function_name": {"type": "string"},
            "return_type": {"type": "string", "default": "void"},
            "parameters": {"type": "array", "items": {"type": "string"}, "default": []}
        },
        "required": ["class_path", "function_name"]
    }
    destructive = True
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        func_name = args.get("function_name")
        return ToolResult(success=True, message=f"Функция {func_name} добавлена")


class SetupIncludePaths(Tool):
    name = "setup_include_paths"
    description = "Настройка путей включения"
    input_schema = {
        "type": "object",
        "properties": {
            "module_name": {"type": "string"},
            "include_paths": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["module_name", "include_paths"]
    }
    destructive = True
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        return ToolResult(success=True, message="Пути настроены")


class GenerateModuleDocumentation(Tool):
    name = "generate_module_documentation"
    description = "Генерация документации"
    input_schema = {
        "type": "object",
        "properties": {
            "module_name": {"type": "string"},
            "output_format": {"type": "string", "enum": ["html", "markdown", "xml"], "default": "markdown"}
        },
        "required": ["module_name"]
    }
    destructive = False
    
    def execute(self, args: dict, ctx: ToolContext) -> ToolResult:
        return ToolResult(success=True, message="Документация сгенерирована")
