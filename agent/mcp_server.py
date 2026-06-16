#!/usr/bin/env python3
"""
Navi-LocalRAG MCP Server
Extiende herramientas para el agente local-rag-dev.
Git, tests, GitHub Actions, análisis de código.
"""

import sys
import os
import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

PROJECT_PATH = str(Path(__file__).parent.parent)
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
GITHUB_USER = os.getenv('GITHUB_USER', 'Gatoco')

server = Server("navi-localrag")

def run_cmd(cmd, timeout=60, cwd=None):
    """Ejecuta comando en el proyecto local-rag con venv activado."""
    if cwd is None:
        cwd = PROJECT_PATH
    venv_python = str(Path(cwd) / ".venv" / "bin" / "python")
    full_cmd = f"cd {cwd} && {venv_python} -c '{cmd}'"
    result = subprocess.run(
        ['bash', '-c', full_cmd],
        capture_output=True, text=True, timeout=timeout
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def run_gh_cmd(cmd, timeout=30):
    """Ejecuta comando gh (GitHub CLI) con auth."""
    result = subprocess.run(
        ['bash', '-c', f'export GH_TOKEN={GITHUB_TOKEN} && {cmd}'],
        capture_output=True, text=True, timeout=timeout
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode

# ==================== TOOLS ====================

@server.list_tools()
async def list_tools():
    return [
        # Git operations
        Tool(
            name="localrag_git_status",
            description="Obtiene estado del repositorio Git",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="localrag_git_branch",
            description="Lista branches o crea nueva",
            inputSchema={
                "type": "object",
                "properties": {
                    "create": {"type": "string", "description": "Nombre de branch a crear (opcional)"}
                }
            }
        ),
        Tool(
            name="localrag_git_commit",
            description="Hace commit con mensaje",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Mensaje de commit"}
                },
                "required": ["message"]
            }
        ),
        Tool(
            name="localrag_git_log",
            description="Muestra últimos commits",
            inputSchema={
                "type": "object",
                "properties": {
                    "count": {"type": "number", "description": "Número de commits a mostrar (default: 10)"}
                }
            }
        ),

        # Testing
        Tool(
            name="localrag_run_tests",
            description="Ejecuta tests (unit, integration, o all)",
            inputSchema={
                "type": "object",
                "properties": {
                    "suite": {"type": "string", "description": "Suite: unit, integration, benchmark, o all (default: all)"}
                }
            }
        ),
        Tool(
            name="localrag_lint",
            description="Ejecuta ruff lint",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),

        # GitHub Actions
        Tool(
            name="localrag_ci_status",
            description="Ver estado de GitHub Actions CI",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="localrag_ci_runs",
            description="Lista recent workflow runs",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "number", "description": "Número de runs a mostrar (default: 5)"}
                }
            }
        ),
        Tool(
            name="localrag_trigger_workflow",
            description="Dispara un workflow de GitHub Actions (con aprobación)",
            inputSchema={
                "type": "object",
                "properties": {
                    "workflow": {"type": "string", "description": "Nombre del workflow archivo .yml"}
                }
            }
        ),

        # Code analysis
        Tool(
            name="localrag_code_quality",
            description="Ejecuta ruff check y muestra warnings/errors",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="localrag_find_bugs",
            description="Busca bugs comunes en código (print statements, TODOs, FIXME, etc)",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Patrón a buscar (default: 'TODO|FIXME|print')"}
                }
            }
        ),

        # Project specific
        Tool(
            name="localrag_ingest_status",
            description="Ver estado del índice de documentos",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="localrag_logs",
            description="Muestra últimas entradas de logs",
            inputSchema={
                "type": "object",
                "properties": {
                    "count": {"type": "number", "description": "Número de líneas (default: 50)"}
                }
            }
        ),

        # Session management
        Tool(
            name="localrag_agent_log",
            description="Registra actividad del agente",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Tipo de acción"},
                    "details": {"type": "string", "description": "Detalles"}
                },
                "required": ["action"]
            }
        ),
        Tool(
            name="localrag_session_report",
            description="Genera reporte de sesión de trabajo",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "localrag_git_status":
            return await git_status()
        elif name == "localrag_git_branch":
            return await git_branch(arguments.get("create"))
        elif name == "localrag_git_commit":
            return await git_commit(arguments.get("message", ""))
        elif name == "localrag_git_log":
            return await git_log(arguments.get("count", 10))
        elif name == "localrag_run_tests":
            return await run_tests(arguments.get("suite", "all"))
        elif name == "localrag_lint":
            return await lint()
        elif name == "localrag_ci_status":
            return await ci_status()
        elif name == "localrag_ci_runs":
            return await ci_runs(arguments.get("limit", 5))
        elif name == "localrag_trigger_workflow":
            return await trigger_workflow(arguments.get("workflow", ""))
        elif name == "localrag_code_quality":
            return await code_quality()
        elif name == "localrag_find_bugs":
            return await find_bugs(arguments.get("pattern", "TODO|FIXME|print"))
        elif name == "localrag_ingest_status":
            return await ingest_status()
        elif name == "localrag_logs":
            return await logs(arguments.get("count", 50))
        elif name == "localrag_agent_log":
            return await agent_log(arguments.get("action", ""), arguments.get("details", ""))
        elif name == "localrag_session_report":
            return await session_report()
        else:
            return [TextContent(type="text", text=f"Tool {name} not found")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

# ==================== IMPLEMENTATIONS ====================

async def git_status():
    out, err, code = run_cmd("git status -s")
    if code != 0:
        return [TextContent(type="text", text=f"Error git: {err}")]
    if not out:
        return [TextContent(type="text", text="Repo limpio, sin cambios pendientes")]
    return [TextContent(type="text", text=f"Cambios pendientes:\n{out}")]

async def git_branch(create=None):
    out, err, code = run_cmd("git branch")
    if code != 0:
        return [TextContent(type="text", text=f"Error: {err}")]
    branches = [b.strip().replace("* ", "") for b in out.split("\n") if b]
    current = [b for b in branches if b.startswith("*")]
    others = [b for b in branches if not b.startswith("*")]
    
    if create:
        out2, err2, code2 = run_cmd(f"git checkout -b agent/{create}")
        if code2 != 0:
            return [TextContent(type="text", text=f"Error creando branch: {err2}")]
        return [TextContent(type="text", text=f"Branch agent/{create} creado y activado")]
    
    result = f"Branch actual: {current[0] if current else 'unknown'}\n"
    result += f"Otras branches: {', '.join(others[:10])}"
    return [TextContent(type="text", text=result)]

async def git_commit(message):
    out, err, code = run_cmd("git status -s")
    if code != 0:
        return [TextContent(type="text", text=f"Error: {err}")]
    if not out.strip():
        return [TextContent(type="text", text="Nada que commitear - repo limpio")]
    
    out2, err2, code2 = run_cmd(f"git add -A && git commit -m '{message}'")
    if code2 != 0:
        return [TextContent(type="text", text=f"Error en commit: {err2}")]
    return [TextContent(type="text", text=f"Commit exitoso:\n{message}")]

async def git_log(count=10):
    out, err, code = run_cmd(f"git log --oneline -n {count}")
    if code != 0:
        return [TextContent(type="text", text=f"Error: {err}")]
    return [TextContent(type="text", text=f"Últimos {count} commits:\n{out}")]

async def run_tests(suite="all"):
    if suite == "unit":
        cmd = "pytest tests/unit/ -v --tb=short"
    elif suite == "integration":
        cmd = "pytest tests/integration/ -v --tb=short"
    elif suite == "benchmark":
        cmd = "pytest tests/benchmarks/ -v --tb=short"
    else:
        cmd = "pytest -v --tb=short"
    
    out, err, code = run_cmd(cmd, timeout=120)
    result = f"Tests {suite}:\n"
    if code == 0:
        result += "✓ TODOS PASARON\n"
    else:
        result += "✗ HAY FALLOS\n"
    result += out[-1500:] if len(out) > 1500 else out
    return [TextContent(type="text", text=result)]

async def lint():
    out, err, code = run_cmd("ruff check src/ tests/")
    if code == 0:
        return [TextContent(type="text", text="Ruff: Sin warnings ni errores")]
    return [TextContent(type="text", text=f"Ruff issues:\n{out[-1500:]}")]

async def ci_status():
    if not GITHUB_TOKEN:
        return [TextContent(type="text", text="GH_TOKEN no configurado")]
    out, err, code = run_gh_cmd(f"gh run list --repo {GITHUB_USER}/local-rag --limit 3 --json status,conclusion,name")
    if code != 0:
        return [TextContent(type="text", text=f"Error consultando CI: {err}")]
    try:
        data = json.loads(out) if out else []
        if not data:
            return [TextContent(type="text", text="No hay workflows recientes")]
        result = "Estado CI:\n"
        for r in data[:5]:
            status = r.get('status', 'unknown')
            conclusion = r.get('conclusion', '')
            name = r.get('name', 'unknown')
            result += f"- {name}: {status} {conclusion}\n"
        return [TextContent(type="text", text=result)]
    except:
        return [TextContent(type="text", text=f"Error parsing CI: {out}")]

async def ci_runs(limit=5):
    if not GITHUB_TOKEN:
        return [TextContent(type="text", text="GH_TOKEN no configurado")]
    out, err, code = run_gh_cmd(f"gh run list --repo {GITHUB_USER}/local-rag --limit {limit}")
    if code != 0:
        return [TextContent(type="text", text=f"Error: {err}")]
    return [TextContent(type="text", text=f"Workflow runs:\n{out}")]

async def trigger_workflow(workflow):
    if not workflow:
        return [TextContent(type="text", text="Nombre de workflow requerido")]
    if not GITHUB_TOKEN:
        return [TextContent(type="text", text="GH_TOKEN no configurado")]
    out, err, code = run_gh_cmd(f"gh workflow run {workflow} --repo {GITHUB_USER}/local-rag")
    if code != 0:
        return [TextContent(type="text", text=f"Error disparando workflow: {err}")]
    return [TextContent(type="text", text=f"Workflow {workflow} disparado")]

async def code_quality():
    out, err, code = run_cmd("ruff check src/ tests/ --output-format=text")
    if code == 0:
        return [TextContent(type="text", text="Código limpio - sin issues")]
    return [TextContent(type="text", text=f"Issues encontrados:\n{out[-2000:]}")]

async def find_bugs(pattern="TODO|FIXME|print"):
    out, err, code = run_cmd(f"grep -r -n -E '{pattern}' src/ tests/ --include='*.py' 2>/dev/null | head -30")
    if code != 0 or not out.strip():
        return [TextContent(type="text", text=f"No se encontraron matches de {pattern}")]
    return [TextContent(type="text", text=f"Findings ({pattern}):\n{out[:2000]}")]

async def ingest_status():
    index_file = Path(PROJECT_PATH) / "chroma_db" / "indexed_manifest.json"
    if not index_file.exists():
        return [TextContent(type="text", text="No hay manifest de índice")]
    try:
        with open(index_file) as f:
            data = json.load(f)
        count = data.get('file_count', 'unknown')
        last = data.get('last_indexed', 'unknown')
        return [TextContent(type="text", text=f"Índice: {count} archivos\nÚltima indexación: {last}")]
    except:
        return [TextContent(type="text", text="Error leyendo índice")]

async def logs(count=50):
    log_file = Path(PROJECT_PATH) / "logs" / "rag.log"
    if not log_file.exists():
        return [TextContent(type="text", text="No hay logs")]
    with open(log_file) as f:
        lines = f.readlines()
    recent = lines[-count:]
    return [TextContent(type="text", text=f"Últimas {count} líneas de logs:\n{''.join(recent)[-2000:]}")]

async def agent_log(action, details=""):
    log_dir = Path(PROJECT_PATH) / "agent" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = log_dir / f"{today}.log"
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, 'a') as f:
        f.write(f"[{timestamp}] {action}: {details}\n")
    return [TextContent(type="text", text=f"Log guardado: {action}")]

async def session_report():
    out, err, code = run_cmd("git status -s")
    changes = out.strip() if out.strip() else "ninguno"
    
    out2, err2, code2 = run_cmd("git log --oneline -n 5")
    recent_commits = out2.strip() if out2.strip() else "ninguno"
    
    return [TextContent(type="text", text=f"""Reporte de sesión:
Estado repo: {changes}
Commits recientes:
{recent_commits}
""")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())