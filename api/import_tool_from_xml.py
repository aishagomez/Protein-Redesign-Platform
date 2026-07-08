import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

from database import SessionLocal
from models import ServiceType, Tool, ToolRuntime, ToolParameter


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes"}


def _get_or_create_service_type(db, stage_name: str) -> ServiceType:
    service_type = db.query(ServiceType).filter(ServiceType.name == stage_name).first()
    if service_type:
        return service_type

    service_type = ServiceType(
        name=stage_name,
        description=f"Tipo de servicio generado desde XML para la etapa '{stage_name}'",
    )
    db.add(service_type)
    db.flush()
    return service_type


def _build_param_payload(node: ET.Element, *, default_input: bool = False, default_output: bool = False) -> dict:
    name = node.attrib["name"]
    return {
        "name": name,
        "flag": node.attrib.get("flag"),
        "data_type": node.attrib.get("type") or node.attrib.get("kind") or "string",
        "optional": not _as_bool(node.attrib.get("required"), default=False),
        "default_value": node.attrib.get("default"),
        "format": node.attrib.get("format"),
        "position": int(node.attrib["positional"]) if node.attrib.get("positional") else None,
        "is_input": _as_bool(node.attrib.get("is_input"), default=default_input),
        "is_output": _as_bool(node.attrib.get("is_output"), default=default_output),
        "ui_label": node.attrib.get("label") or name,
        "options": None,
        "description": node.attrib.get("description"),
    }


def _parse_runtime(root: ET.Element) -> dict | None:
    runtime_node = root.find("runtime")
    if runtime_node is None:
        return None

    mounts = []
    mounts_node = runtime_node.find("mounts")
    if mounts_node is not None:
        for mount in mounts_node.findall("mount"):
            mounts.append({
                "name": mount.attrib.get("name"),
                "source_param": mount.attrib.get("source_param"),
                "target": mount.attrib.get("target"),
                "read_only": _as_bool(mount.attrib.get("read_only"), default=False),
            })

    env = {}
    env_node = runtime_node.find("env")
    if env_node is not None:
        for item in env_node.findall("var"):
            env[item.attrib["name"]] = item.attrib.get("value", "")

    resources = {}
    resources_node = runtime_node.find("resources")
    if resources_node is not None:
        if resources_node.attrib.get("memory"):
            resources["memory"] = resources_node.attrib["memory"]
        if resources_node.attrib.get("cpus"):
            resources["cpus"] = resources_node.attrib["cpus"]

    command_template = []
    command_node = runtime_node.find("command")
    if command_node is not None:
        for arg in command_node.findall("arg"):
            if arg.text:
                command_template.append(arg.text.strip())

    return {
        "mode": runtime_node.attrib.get("mode", "docker"),
        "image": runtime_node.findtext("image"),
        "workdir": runtime_node.findtext("workdir"),
        "command_template": command_template,
        "mounts": mounts,
        "env": env,
        "resources": resources,
        "notes": runtime_node.findtext("notes"),
    }


def import_tool_from_xml(xml_path: str) -> Tool:
    xml_file = Path(xml_path)
    raw_xml = xml_file.read_text(encoding="utf-8")
    root = ET.fromstring(raw_xml)

    if root.tag != "tool":
        raise ValueError("El XML debe tener un nodo raiz <tool>")

    stage_name = root.attrib.get("stage")
    if not stage_name:
        raise ValueError("El XML debe incluir el atributo stage en <tool>")

    tool_name = root.attrib.get("name")
    if not tool_name:
        raise ValueError("El XML debe incluir el atributo name en <tool>")

    db = SessionLocal()
    try:
        service_type = _get_or_create_service_type(db, stage_name)

        tool = (
            db.query(Tool)
            .filter(Tool.name == tool_name, Tool.version == root.attrib.get("version"))
            .first()
        )
        if not tool:
            tool = Tool(name=tool_name)
            db.add(tool)

        runtime_data = _parse_runtime(root)
        description = root.findtext("description")

        tool.service_type_id = service_type.id
        tool.version = root.attrib.get("version")
        tool.description = description
        tool.executable_path = None
        tool.definition_format = "xml"
        tool.definition_source = raw_xml
        tool.active = _as_bool(root.attrib.get("active"), default=True)

        db.flush()

        runtime = db.query(ToolRuntime).filter(ToolRuntime.tool_id == tool.id).first()
        if runtime_data:
            if runtime is None:
                runtime = ToolRuntime(tool_id=tool.id)
                db.add(runtime)
            for field, value in runtime_data.items():
                setattr(runtime, field, value)
        elif runtime is not None:
            db.delete(runtime)

        db.query(ToolParameter).filter(ToolParameter.tool_id == tool.id).delete()

        parameters = []
        for section_name, default_input, default_output in (
            ("inputs", True, False),
            ("options", False, False),
            ("outputs", False, True),
        ):
            section = root.find(section_name)
            if section is None:
                continue
            for child in list(section):
                if child.tag not in {"param", "artifact"}:
                    continue
                parameters.append(
                    ToolParameter(
                        tool_id=tool.id,
                        **_build_param_payload(
                            child,
                            default_input=default_input,
                            default_output=default_output,
                        ),
                    )
                )

        for parameter in parameters:
            db.add(parameter)

        db.commit()
        db.refresh(tool)
        return tool
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def import_tools_from_directory(directory_path: str) -> list[Tool]:
    base_path = Path(directory_path)
    if not base_path.exists():
        return []

    imported_tools = []
    for xml_file in sorted(base_path.glob("*.xml")):
        imported_tools.append(import_tool_from_xml(str(xml_file)))
    return imported_tools


def main():
    parser = argparse.ArgumentParser(description="Crear o actualizar una herramienta desde un XML")
    parser.add_argument("xml_path", help="Ruta del archivo XML de definicion")
    args = parser.parse_args()

    tool = import_tool_from_xml(args.xml_path)
    print(f"Herramienta importada: id={tool.id}, name={tool.name}, version={tool.version}")


if __name__ == "__main__":
    main()
