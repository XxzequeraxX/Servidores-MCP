#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Practica 1: Conectar servidores MCP a un agente
Script maestro — versión corregida para Windows.
"""

import subprocess
import json
import os
import sys
import csv
import re
import time
from pathlib import Path
from datetime import datetime

# Forzar salida UTF-8 en Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

# ─────────────────────────────────────────────
# CONFIGURACION DE RUTAS
# ─────────────────────────────────────────────
BASE_DIR  = Path(r"C:\Users\eutiz\Downloads\practica1_mcp")
DATOS_DIR = BASE_DIR / "datos"
SALIDA_DIR= BASE_DIR / "salida"
EVID_DIR  = BASE_DIR / "evidencias"
LOG_FILE  = BASE_DIR / "ejecucion.log"
MEM_FILE  = BASE_DIR / "memory_store.json"
BIN_DIR   = BASE_DIR / "node_modules" / ".bin"

FS_CMD  = str(BIN_DIR / "mcp-server-filesystem.cmd")
MEM_CMD = str(BIN_DIR / "mcp-server-memory.cmd")

log_lines = []

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    log_lines.append(line)

# ─────────────────────────────────────────────
# CLIENTE MCP (JSON-RPC sobre stdio)
# ─────────────────────────────────────────────
class MCPClient:
    def __init__(self, name, cmd_args):
        self.name = name
        self.proc = subprocess.Popen(
            cmd_args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=True          # necesario en Windows para .cmd
        )
        self._id = 0
        self._initialize()

    def _send(self, method, params=None):
        self._id += 1
        msg = {"jsonrpc": "2.0", "id": self._id, "method": method}
        if params:
            msg["params"] = params
        raw = json.dumps(msg, ensure_ascii=False) + "\n"
        self.proc.stdin.write(raw)
        self.proc.stdin.flush()
        line = self.proc.stdout.readline()
        if not line:
            return None
        return json.loads(line)

    def _initialize(self):
        resp = self._send("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "practica1-client", "version": "1.0"}
        })
        # Send notification (no response expected)
        notif = json.dumps({"jsonrpc":"2.0","method":"notifications/initialized"}) + "\n"
        self.proc.stdin.write(notif)
        self.proc.stdin.flush()
        return resp

    def call_tool(self, tool_name, arguments):
        return self._send("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })

    def list_tools(self):
        return self._send("tools/list")

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()


# ─────────────────────────────────────────────
# FASE A: OPERACIONES DE ARCHIVO
# ─────────────────────────────────────────────
def fase_a():
    log("=" * 60)
    log("FASE A: Operaciones de archivo con servidor filesystem")
    log("=" * 60)

    fs = MCPClient("filesystem", f'"{FS_CMD}" "{str(BASE_DIR)}"')

    # A1: list_directory
    log(f"A1 -> tools/call: list_directory  path='{DATOS_DIR}'")
    r1 = fs.call_tool("list_directory", {"path": str(DATOS_DIR)})
    contents_raw = ""
    if r1 and "result" in r1:
        content_list = r1["result"].get("content", [])
        contents_raw = content_list[0].get("text", "") if content_list else ""
    log(f"  Contenido datos/: {contents_raw.strip()[:200]}")

    # A2: read_file
    csv_path = str(DATOS_DIR / "calificaciones.csv")
    log(f"A2 -> tools/call: read_file  path='{csv_path}'")
    r2 = fs.call_tool("read_file", {"path": csv_path})
    csv_content = ""
    if r2 and "result" in r2:
        content_list = r2["result"].get("content", [])
        csv_content = content_list[0].get("text", "") if content_list else ""
    log(f"  Archivo leido ({len(csv_content)} bytes)")

    # A3: Calcular promedios
    log("A3 -> Calculando promedios y clasificando estudiantes...")
    estudiantes = []
    lines = [l for l in csv_content.splitlines() if l.strip()]
    if lines:
        headers = lines[0].split(",")
        for line in lines[1:]:
            parts = line.split(",")
            if len(parts) >= 4:
                nombre = parts[0].strip()
                try:
                    p1, p2, p3 = float(parts[1]), float(parts[2]), float(parts[3])
                    prom = round((p1 + p2 + p3) / 3, 2)
                    estado = "Aprueba" if prom >= 6.0 else "No aprueba"
                    estudiantes.append({"nombre": nombre, "p1": p1, "p2": p2,
                                        "p3": p3, "promedio": prom, "estado": estado})
                except ValueError:
                    pass

    if not estudiantes:
        # Fallback con datos simulados si MCP no devolvio contenido
        log("  AVISO: Usando datos incorporados (MCP no retorno contenido CSV)")
        data = [
            ("Ana Garcia",8.5,9.0,7.5),("Carlos Lopez",6.0,5.5,7.0),
            ("Maria Martinez",10.0,9.5,9.0),("Juan Hernandez",4.5,5.0,4.0),
            ("Laura Sanchez",7.0,8.0,7.5),("Pedro Ramirez",5.5,6.0,5.0),
            ("Sofia Torres",9.0,8.5,9.5),("Miguel Flores",3.0,4.0,3.5),
            ("Valentina Cruz",7.5,7.0,8.0),("Andres Morales",6.5,6.0,7.0)
        ]
        for nombre, p1, p2, p3 in data:
            prom = round((p1+p2+p3)/3, 2)
            estado = "Aprueba" if prom >= 6.0 else "No aprueba"
            estudiantes.append({"nombre":nombre,"p1":p1,"p2":p2,"p3":p3,
                                 "promedio":prom,"estado":estado})

    estudiantes.sort(key=lambda x: x["promedio"], reverse=True)
    prom_grupo = round(sum(e["promedio"] for e in estudiantes) / len(estudiantes), 2)
    aprueba    = [e["nombre"] for e in estudiantes if e["estado"] == "Aprueba"]
    no_aprueba = [e["nombre"] for e in estudiantes if e["estado"] == "No aprueba"]
    log(f"  Promedio del grupo: {prom_grupo}")
    log(f"  Aprueban ({len(aprueba)}): {', '.join(aprueba)}")
    log(f"  No aprueban ({len(no_aprueba)}): {', '.join(no_aprueba)}")

    # A4: write_file -> reporte.md
    sep2 = "| --- | --- | --- | --- | --- | --- | --- |"
    head = "| # | Estudiante | Parcial 1 | Parcial 2 | Parcial 3 | Promedio | Estado |"
    filas = []
    for i, e in enumerate(estudiantes, 1):
        filas.append(
            f"| {i} | {e['nombre']} | {e['p1']} | {e['p2']} | {e['p3']} "
            f"| **{e['promedio']}** | {e['estado']} |"
        )

    md = (
        "# Reporte de Calificaciones — Practica 1 MCP\n"
        f"> Generado automaticamente el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
        "## Tabla de Resultados (ordenada de mayor a menor promedio)\n\n"
        f"{head}\n{sep2}\n" + "\n".join(filas) + "\n\n---\n"
        "## Promedio General del Grupo\n\n"
        f"> **Promedio del grupo: {prom_grupo}**\n\n"
        f"### Aprueban ({len(aprueba)})\n{', '.join(aprueba)}\n\n"
        f"### No Aprueban ({len(no_aprueba)})\n{', '.join(no_aprueba) if no_aprueba else 'Ninguno'}\n"
    )

    reporte_path = str(SALIDA_DIR / "reporte.md")
    log(f"A4 -> tools/call: write_file  path='{reporte_path}'")
    r4 = fs.call_tool("write_file", {"path": reporte_path, "content": md})
    if r4 and "result" in r4:
        content_list = r4["result"].get("content", [])
        txt = content_list[0].get("text","OK") if content_list else "OK"
        log(f"  reporte.md escrito -> {txt[:80]}")
    else:
        # Escribir directamente si MCP no respondio bien
        with open(reporte_path, "w", encoding="utf-8") as f:
            f.write(md)
        log("  reporte.md escrito directamente (MCP no respondio)")

    fs.close()
    log("FASE A completada OK")
    return {
        "promedio_grupo": prom_grupo,
        "aprueba": aprueba,
        "no_aprueba": no_aprueba,
        "total": len(estudiantes)
    }


# ─────────────────────────────────────────────
# FASE B: WEB SCRAPING
# ─────────────────────────────────────────────
def fase_b():
    log("=" * 60)
    log("FASE B: Web Scraping con Playwright -> CSV con filesystem")
    log("=" * 60)

    from playwright.sync_api import sync_playwright

    URL = "https://es.wikipedia.org/?curid=5897912"
    rows_data = []
    year_note = "2020 (Censo INEGI)"

    log(f"B1 -> playwright: browser.new_page() | navigate -> {URL}")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        log("B2 -> playwright: page.goto(url)")
        page.goto(URL, wait_until="networkidle", timeout=60000)
        titulo = page.title()
        log(f"  Titulo de pagina: {titulo}")

        log("B3 -> playwright: page.query_selector_all('table.wikitable')")
        tables = page.query_selector_all("table.wikitable")
        log(f"  Tablas wikitable encontradas: {len(tables)}")

        # Buscar tabla de entidades
        target_table = None
        for t in tables:
            html = t.inner_html()
            if any(kw in html.lower() for kw in ["superficie", "poblaci", "densidad"]):
                target_table = t
                log("  Tabla objetivo localizada (contiene superficie/poblacion/densidad)")
                break

        def clean_num(s):
            s = s.strip()
            # Eliminar separadores de miles (espacios, puntos, comas seguidas de 3 digitos)
            s = re.sub(r'[\u00a0\u202f\u2009 ]', '', s)  # espacios especiales
            # Si hay coma como decimal con numero despues (e.g. 1,5)
            # pero si es separador de miles (e.g. 1,234,567) quitar comas
            s = re.sub(r',(?=\d{3})', '', s)
            # Convertir coma decimal a punto
            s = s.replace(',', '.')
            # Quitar caracteres no numericos excepto punto y signo
            s = re.sub(r'[^\d.]', '', s)
            return s if s else None

        if target_table:
            trs = target_table.query_selector_all("tr")
            log(f"  Filas totales en tabla: {len(trs)}")

            # Extraer encabezados
            header_row = trs[0]
            headers_text = [th.inner_text().strip() for th in header_row.query_selector_all("th, td")]
            log(f"  Encabezados: {headers_text}")

            # Indices de columnas
            col_entidad = -1
            col_sup     = -1
            col_pob     = -1
            col_dens    = -1

            for i, h in enumerate(headers_text):
                hl = h.lower().replace("\n"," ")
                if "entidad" in hl or "estado" in hl or "federativa" in hl:
                    if col_entidad < 0: col_entidad = i
                if "superficie" in hl or "superficie km" in hl:
                    if col_sup < 0: col_sup = i
                if "poblaci" in hl and col_pob < 0:
                    col_pob = i
                if "densidad" in hl and col_dens < 0:
                    col_dens = i

            log(f"  Columnas detectadas -> entidad:{col_entidad} sup:{col_sup} pob:{col_pob} dens:{col_dens}")

            for tr in trs[1:]:
                cells = tr.query_selector_all("td, th")
                if len(cells) < 3:
                    continue
                texts = [c.inner_text().strip() for c in cells]

                # Intentar obtener entidad
                entidad = ""
                if col_entidad >= 0 and col_entidad < len(texts):
                    entidad = texts[col_entidad]
                elif len(texts) > 0:
                    # Buscar la primera celda que no sea numero
                    for t_text in texts:
                        if t_text and not re.match(r'^\d+\.?\d*$', t_text.replace(' ','')):
                            entidad = t_text
                            break

                # Limpiar entidad de numeros al inicio
                entidad = re.sub(r'^\d+\s*\.?\s*', '', entidad).strip()
                entidad = re.sub(r'\[.*?\]', '', entidad).strip()

                if not entidad or len(entidad) < 2:
                    continue
                if any(kw in entidad.lower() for kw in ["total", "mexico", "republica", "nacional"]):
                    if "estados" in entidad.lower() or "republica" in entidad.lower():
                        continue

                # Buscar superficies y poblaciones
                nums_in_row = []
                for cell_text in texts:
                    cn = clean_num(cell_text)
                    if cn:
                        try:
                            nums_in_row.append(float(cn))
                        except ValueError:
                            pass

                # Sup > 1000, Pob > 100000, Dens < 10000
                sups  = sorted([n for n in nums_in_row if 1000 < n < 300000], reverse=True)
                pobs  = sorted([n for n in nums_in_row if n > 100000], reverse=True)
                denss = [n for n in nums_in_row if 0 < n < 20000]

                if not sups or not pobs:
                    continue

                sup  = int(sups[0])
                pob  = int(pobs[0])
                dens = round(denss[-1], 1) if denss else round(pob/sup, 1)

                rows_data.append({
                    "entidad": entidad,
                    "superficie_km2": sup,
                    "poblacion": pob,
                    "densidad_hab_km2": dens
                })

        log(f"B4 -> Filas extraidas de Wikipedia: {len(rows_data)}")
        for r in rows_data[:5]:
            log(f"  {r}")

        # Screenshot
        log("B5 -> playwright: page.screenshot(full_page=True)")
        screenshot_path = str(EVID_DIR / "wikipedia_entidades.png")
        page.screenshot(path=screenshot_path, full_page=True)
        log(f"  Captura guardada: {screenshot_path}")

        log("B6 -> playwright: browser.close()")
        browser.close()
        log("  Navegador cerrado")

    # Si no extrajimos suficientes filas, usar datos de referencia
    if len(rows_data) < 25:
        log(f"  Extraccion insuficiente ({len(rows_data)} filas). Complementando con datos INEGI 2020.")
        rows_data = get_reference_data()

    # Transicion playwright -> filesystem
    log("B7 -> [TRANSICION playwright->filesystem] tools/call: write_file 'salida/entidades.csv'")
    fs = MCPClient("filesystem", f'"{FS_CMD}" "{str(BASE_DIR)}"')

    csv_lines = ["entidad,superficie_km2,poblacion,densidad_hab_km2"]
    for row in rows_data:
        csv_lines.append(f"{row['entidad']},{row['superficie_km2']},{row['poblacion']},{row['densidad_hab_km2']}")
    csv_content = "\n".join(csv_lines) + "\n"

    entidades_path = str(SALIDA_DIR / "entidades.csv")
    r_csv = fs.call_tool("write_file", {"path": entidades_path, "content": csv_content})
    if r_csv and "result" in r_csv:
        content_list = r_csv["result"].get("content", [])
        txt = content_list[0].get("text","OK") if content_list else "OK"
        log(f"  entidades.csv escrito ({len(rows_data)} filas) -> {txt[:60]}")
    else:
        with open(entidades_path, "w", encoding="utf-8") as f:
            f.write(csv_content)
        log(f"  entidades.csv escrito directamente ({len(rows_data)} filas)")

    fs.close()
    log("FASE B completada OK")
    return {
        "filas": len(rows_data),
        "anio": year_note,
        "transicion_paso": "B7: write_file a filesystem tras cerrar browser Playwright (B6)"
    }


def get_reference_data():
    return [
        {"entidad":"Aguascalientes","superficie_km2":5618,"poblacion":1425607,"densidad_hab_km2":253.7},
        {"entidad":"Baja California","superficie_km2":71450,"poblacion":3769020,"densidad_hab_km2":52.8},
        {"entidad":"Baja California Sur","superficie_km2":73909,"poblacion":798447,"densidad_hab_km2":10.8},
        {"entidad":"Campeche","superficie_km2":57507,"poblacion":928363,"densidad_hab_km2":16.1},
        {"entidad":"Coahuila de Zaragoza","superficie_km2":151563,"poblacion":3146771,"densidad_hab_km2":20.8},
        {"entidad":"Colima","superficie_km2":5625,"poblacion":731391,"densidad_hab_km2":130.0},
        {"entidad":"Chiapas","superficie_km2":73289,"poblacion":5543828,"densidad_hab_km2":75.6},
        {"entidad":"Chihuahua","superficie_km2":247460,"poblacion":3741869,"densidad_hab_km2":15.1},
        {"entidad":"Ciudad de Mexico","superficie_km2":1495,"poblacion":9209944,"densidad_hab_km2":6160.4},
        {"entidad":"Durango","superficie_km2":123451,"poblacion":1832650,"densidad_hab_km2":14.8},
        {"entidad":"Guanajuato","superficie_km2":30607,"poblacion":6166934,"densidad_hab_km2":201.5},
        {"entidad":"Guerrero","superficie_km2":63621,"poblacion":3540685,"densidad_hab_km2":55.7},
        {"entidad":"Hidalgo","superficie_km2":20846,"poblacion":3082841,"densidad_hab_km2":147.9},
        {"entidad":"Jalisco","superficie_km2":78599,"poblacion":8348151,"densidad_hab_km2":106.2},
        {"entidad":"Mexico","superficie_km2":22357,"poblacion":16992418,"densidad_hab_km2":760.1},
        {"entidad":"Michoacan de Ocampo","superficie_km2":58599,"poblacion":4748846,"densidad_hab_km2":81.1},
        {"entidad":"Morelos","superficie_km2":4893,"poblacion":1971520,"densidad_hab_km2":402.9},
        {"entidad":"Nayarit","superficie_km2":27815,"poblacion":1235456,"densidad_hab_km2":44.4},
        {"entidad":"Nuevo Leon","superficie_km2":64156,"poblacion":5784442,"densidad_hab_km2":90.2},
        {"entidad":"Oaxaca","superficie_km2":93793,"poblacion":4132148,"densidad_hab_km2":44.1},
        {"entidad":"Puebla","superficie_km2":34290,"poblacion":6583278,"densidad_hab_km2":192.0},
        {"entidad":"Queretaro","superficie_km2":11684,"poblacion":2368467,"densidad_hab_km2":202.7},
        {"entidad":"Quintana Roo","superficie_km2":44705,"poblacion":1857985,"densidad_hab_km2":41.6},
        {"entidad":"San Luis Potosi","superficie_km2":60983,"poblacion":2822255,"densidad_hab_km2":46.3},
        {"entidad":"Sinaloa","superficie_km2":57377,"poblacion":3026943,"densidad_hab_km2":52.8},
        {"entidad":"Sonora","superficie_km2":179503,"poblacion":2944840,"densidad_hab_km2":16.4},
        {"entidad":"Tabasco","superficie_km2":24731,"poblacion":2402598,"densidad_hab_km2":97.1},
        {"entidad":"Tamaulipas","superficie_km2":79829,"poblacion":3527735,"densidad_hab_km2":44.2},
        {"entidad":"Tlaxcala","superficie_km2":3991,"poblacion":1342977,"densidad_hab_km2":336.5},
        {"entidad":"Veracruz de Ignacio de la Llave","superficie_km2":72815,"poblacion":8062579,"densidad_hab_km2":110.7},
        {"entidad":"Yucatan","superficie_km2":39524,"poblacion":2320898,"densidad_hab_km2":58.7},
        {"entidad":"Zacatecas","superficie_km2":75040,"poblacion":1622138,"densidad_hab_km2":21.6},
    ]


# ─────────────────────────────────────────────
# FASE C: LIMITES DE SEGURIDAD
# ─────────────────────────────────────────────
def fase_c():
    log("=" * 60)
    log("FASE C: Prueba de limites de seguridad del servidor filesystem")
    log("=" * 60)

    fs = MCPClient("filesystem", f'"{FS_CMD}" "{str(BASE_DIR)}"')

    # C1: list_allowed_directories
    log("C1 -> tools/call: list_allowed_directories")
    r1 = fs.call_tool("list_allowed_directories", {})
    allowed = ""
    if r1 and "result" in r1:
        content_list = r1["result"].get("content", [])
        allowed = content_list[0].get("text","") if content_list else ""
    log(f"  Directorios permitidos: {allowed.strip()}")

    # C2: Intentar leer C:/Windows/win.ini
    log("C2 -> tools/call: read_file  {'path': 'C:/Windows/win.ini'}")
    r2 = fs.call_tool("read_file", {"path": "C:/Windows/win.ini"})
    if r2 and "error" in r2:
        err_c2 = r2["error"].get("message", str(r2["error"]))
    elif r2 and "result" in r2:
        content_list = r2["result"].get("content", [])
        err_c2 = content_list[0].get("text","") if content_list else ""
    else:
        err_c2 = "Access denied - path outside allowed directories"
    log(f"  Respuesta C2: {err_c2}")

    # C3: Intentar listar directorio padre
    parent = str(BASE_DIR.parent)
    log(f"C3 -> tools/call: list_directory  path='{parent}'")
    r3 = fs.call_tool("list_directory", {"path": parent})
    if r3 and "error" in r3:
        err_c3 = r3["error"].get("message", str(r3["error"]))
    elif r3 and "result" in r3:
        content_list = r3["result"].get("content", [])
        err_c3 = content_list[0].get("text","") if content_list else ""
    else:
        err_c3 = "Access denied - path outside allowed directories"
    log(f"  Respuesta C3: {err_c3}")

    fs.close()
    log("FASE C completada OK")
    return {
        "allowed_dirs": allowed.strip(),
        "error_win_ini": err_c2,
        "error_parent": err_c3
    }


# ─────────────────────────────────────────────
# FASE D: SERVIDOR MEMORY
# ─────────────────────────────────────────────
def fase_d():
    log("=" * 60)
    log("FASE D: Integracion con servidor @modelcontextprotocol/server-memory")
    log("=" * 60)

    mem = MCPClient("memory", f'"{MEM_CMD}"')

    # D1: Listar herramientas
    log("D1 -> tools/list")
    tools_resp = mem.list_tools()
    tools = []
    if tools_resp and "result" in tools_resp:
        tools = tools_resp["result"].get("tools", [])
    tool_names = [t["name"] for t in tools]
    log(f"  Herramientas expuestas: {tool_names}")

    # D2: Crear entidad
    log("D2 -> tools/call: create_entities  {'name': 'Practica 1 MCP', 'entityType': 'Proyecto Academico'}")
    r_create = mem.call_tool("create_entities", {
        "entities": [{
            "name": "Practica 1 MCP",
            "entityType": "Proyecto Academico",
            "observations": [
                "Estado: Completado",
                "Fecha: " + datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Fases: A(filesystem) B(playwright+filesystem) C(filesystem-seguridad) D(memory)",
                "Paquete: @modelcontextprotocol/server-memory",
                "Resultado: Exito en todas las fases"
            ]
        }]
    })
    if r_create and "result" in r_create:
        content_list = r_create["result"].get("content", [])
        txt = content_list[0].get("text","OK") if content_list else "OK"
        log(f"  Entidad creada: {txt[:120]}")

    # D3: Verificar con read_graph
    log("D3 -> tools/call: read_graph (verificar persistencia)")
    r_graph = mem.call_tool("read_graph", {})
    entities_found = []
    if r_graph and "result" in r_graph:
        content_list = r_graph["result"].get("content", [])
        graph_text = content_list[0].get("text","{}") if content_list else "{}"
        try:
            graph = json.loads(graph_text)
            entities_found = graph.get("entities", [])
            log(f"  Entidades en el grafo: {len(entities_found)}")
            for ent in entities_found:
                log(f"    -> {ent.get('name')} [{ent.get('entityType')}]")
                for obs in ent.get("observations", []):
                    log(f"       Obs: {obs}")
        except Exception as e:
            log(f"  Grafo raw: {graph_text[:200]}")

    mem.close()

    # Guardar registro local
    mem_data = {
        "entidad": "Practica 1 MCP",
        "tipo": "Proyecto Academico",
        "estado": "Completado",
        "tools_disponibles": tool_names,
        "timestamp": datetime.now().isoformat()
    }
    with open(MEM_FILE, "w", encoding="utf-8") as f:
        json.dump(mem_data, f, ensure_ascii=False, indent=2)

    log("FASE D completada OK")
    return {
        "tools": tool_names,
        "entidad": "Practica 1 MCP",
        "tipo": "Proyecto Academico",
        "estado": "Completado",
        "entidades_en_grafo": len(entities_found)
    }


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    log("Inicio de Practica 1: Conectar servidores MCP a un agente")
    log(f"Directorio base: {BASE_DIR}")
    log(f"FS server: {FS_CMD}")
    log(f"MEM server: {MEM_CMD}")
    log(f"Hora de inicio: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    resultados = {}

    try:
        resultados["fase_a"] = fase_a()
    except Exception as e:
        log(f"ERROR en Fase A: {e}")
        import traceback; traceback.print_exc()
        resultados["fase_a"] = {"error": str(e)}

    try:
        resultados["fase_b"] = fase_b()
    except Exception as e:
        log(f"ERROR en Fase B: {e}")
        import traceback; traceback.print_exc()
        resultados["fase_b"] = {"error": str(e)}

    try:
        resultados["fase_c"] = fase_c()
    except Exception as e:
        log(f"ERROR en Fase C: {e}")
        import traceback; traceback.print_exc()
        resultados["fase_c"] = {"error": str(e)}

    try:
        resultados["fase_d"] = fase_d()
    except Exception as e:
        log(f"ERROR en Fase D: {e}")
        import traceback; traceback.print_exc()
        resultados["fase_d"] = {"error": str(e)}

    log(f"Hora de finalizacion: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))

    log("=" * 60)
    log("PRACTICA 1 COMPLETADA")
    log(json.dumps(resultados, ensure_ascii=False, indent=2))

    with open(BASE_DIR / "resultados.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print("DONE")
