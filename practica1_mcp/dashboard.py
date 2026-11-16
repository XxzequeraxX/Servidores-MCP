import os
import json
import csv
from flask import Flask, render_template_string

app = Flask(__name__)

# Base directory
BASE_DIR = r"C:\Users\eutiz\Downloads\practica1_mcp"

def get_fase_a_data():
    calificaciones = []
    csv_path = os.path.join(BASE_DIR, "datos", "calificaciones.csv")
    if os.path.exists(csv_path):
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    p1 = float(row.get('parcial1', 0))
                    p2 = float(row.get('parcial2', 0))
                    p3 = float(row.get('parcial3', 0))
                    prom = round((p1 + p2 + p3) / 3, 2)
                    estado = "Aprueba" if prom >= 6.0 else "No aprueba"
                    calificaciones.append({
                        "matricula": row.get('matricula', '').strip(),
                        "nombre": row.get('nombre', '').strip(),
                        "p1": p1, "p2": p2, "p3": p3,
                        "promedio": prom, "estado": estado
                    })
                except ValueError:
                    continue
    calificaciones.sort(key=lambda x: x['promedio'], reverse=True)
    for i, item in enumerate(calificaciones, start=1):
        item['posicion'] = i
        
    avg_group = round(sum(c['promedio'] for c in calificaciones) / len(calificaciones), 2) if calificaciones else 0.0
    passed = sum(1 for c in calificaciones if c['estado'] == "Aprueba")
    failed = len(calificaciones) - passed
    return calificaciones, avg_group, passed, failed

def get_fase_b_data():
    entidades = []
    csv_path = os.path.join(BASE_DIR, "salida", "entidades.csv")
    if os.path.exists(csv_path):
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                entidades.append(row)
    return entidades

def get_fase_d_data():
    memory_path = os.path.join(BASE_DIR, "memory_store.json")
    if os.path.exists(memory_path):
        with open(memory_path, mode='r', encoding='utf-8') as f:
            return json.load(f)
    return {}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>MCP Cyberpunk Dashboard // Práctica 1</title>
    <style>
        :root {
            --bg-color: #0a0a0c;
            --card-bg: #121216;
            --neon-red: #ff0055;
            --neon-red-glow: rgba(255, 0, 85, 0.4);
            --border-color: #2a2a35;
            --text-color: #e0e0e0;
            --muted-text: #8a8a9e;
            --green-accent: #00ff66;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: 'Consolas', 'Courier New', monospace;
            margin: 0;
            padding: 20px;
        }

        .header {
            border-bottom: 2px solid var(--neon-red);
            padding-bottom: 10px;
            margin-bottom: 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 15px var(--neon-red-glow);
        }

        .header h1 {
            color: var(--neon-red);
            margin: 0;
            letter-spacing: 2px;
            text-shadow: 0 0 8px var(--neon-red);
        }

        .badge {
            background: #ff005522;
            border: 1px solid var(--neon-red);
            color: var(--neon-red);
            padding: 5px 12px;
            border-radius: 4px;
            font-size: 0.9em;
        }

        .section-title {
            color: #fff;
            border-left: 4px solid var(--neon-red);
            padding-left: 10px;
            margin-top: 30px;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        .card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0,0,0,0.5);
        }

        .card-highlight {
            border-color: var(--neon-red);
            box-shadow: 0 0 12px var(--neon-red-glow);
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }

        th, td {
            border: 1px solid var(--border-color);
            padding: 8px 12px;
            text-align: left;
            font-size: 0.9em;
        }

        th {
            background-color: #1a1a22;
            color: var(--neon-red);
        }

        tr:nth-child(even) {
            background-color: #16161d;
        }

        .table-container {
            max-height: 350px;
            overflow-y: auto;
        }

        .status-pass { color: var(--green-accent); font-weight: bold; }
        .status-fail { color: var(--neon-red); font-weight: bold; }

        .callout-error {
            background-color: #2b000d;
            border: 1px solid var(--neon-red);
            color: #ff99aa;
            padding: 12px;
            border-radius: 4px;
            font-size: 0.9em;
            margin-bottom: 10px;
        }

        .metric-box {
            display: flex;
            gap: 20px;
            margin-bottom: 15px;
        }

        .metric {
            background: #181820;
            border: 1px solid var(--border-color);
            padding: 10px 15px;
            border-radius: 4px;
            flex: 1;
            text-align: center;
        }

        .metric-val {
            font-size: 1.6em;
            color: var(--neon-red);
            font-weight: bold;
        }

        .metric-lbl {
            font-size: 0.75em;
            color: var(--muted-text);
        }
    </style>
</head>
<body>

    <div class="header">
        <h1>MCP // CYBERPUNK DASHBOARD</h1>
        <span class="badge">SISTEMA ACTIVO // PRÁCTICA 1</span>
    </div>

    <!-- FASE A -->
    <div class="section-title">Fase A — Operaciones de Archivo (filesystem)</div>
    <div class="card card-highlight">
        <div class="metric-box">
            <div class="metric">
                <div class="metric-val">{{ avg_group }}</div>
                <div class="metric-lbl">PROMEDIO GENERAL DE GRUPO</div>
            </div>
            <div class="metric">
                <div class="metric-val" style="color: var(--green-accent);">{{ passed }}</div>
                <div class="metric-lbl">ESTUDIANTES APROBADOS</div>
            </div>
            <div class="metric">
                <div class="metric-val">{{ failed }}</div>
                <div class="metric-lbl">ESTUDIANTES REPROBADOS</div>
            </div>
        </div>

        <h3>Tabla Completa de Calificaciones</h3>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Posición</th>
                        <th>Matrícula</th>
                        <th>Nombre</th>
                        <th>Parcial 1</th>
                        <th>Parcial 2</th>
                        <th>Parcial 3</th>
                        <th>Promedio</th>
                        <th>Estado</th>
                    </tr>
                </thead>
                <tbody>
                    {% for student in calificaciones %}
                    <tr>
                        <td>{{ student.posicion }}</td>
                        <td>{{ student.matricula }}</td>
                        <td>{{ student.nombre }}</td>
                        <td>{{ student.p1 }}</td>
                        <td>{{ student.p2 }}</td>
                        <td>{{ student.p3 }}</td>
                        <td>{{ student.promedio }}</td>
                        <td class="{{ 'status-pass' if student.estado == 'Aprueba' else 'status-fail' }}">{{ student.estado }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <!-- FASE B & C -->
    <div class="grid-2">
        <!-- FASE B -->
        <div>
            <div class="section-title">Fase B — Web Scraping a CSV (playwright + filesystem)</div>
            <div class="card">
                <p><strong style="color: var(--neon-red);">Secuencia:</strong> <code>playwright: browser_navigate</code> &rarr; <code>browser_evaluate</code> &rarr; <code>filesystem: write_file</code></p>
                <p><strong>Entidades extraídas de Wikipedia (32 Estados):</strong></p>
                <div class="table-container" style="max-height: 250px;">
                    <table>
                        <thead>
                            <tr>
                                <th>Entidad</th>
                                <th>Superficie (km²)</th>
                                <th>Población</th>
                                <th>Densidad</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for e in entidades %}
                            <tr>
                                <td>{{ e.entidad }}</td>
                                <td>{{ e.superficie_km2 }}</td>
                                <td>{{ e.poblacion }}</td>
                                <td>{{ e.densidad_hab_km2 }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- FASE C -->
        <div>
            <div class="section-title">Fase C — Límites de Seguridad (filesystem)</div>
            <div class="card">
                <p><strong>Error al intentar leer C:/Windows/win.ini:</strong></p>
                <div class="callout-error">
                    Access denied - path outside allowed directories: C:\\Windows\\win.ini not in C:\\Users\\eutiz\\Downloads\\practica1_mcp
                </div>

                <p><strong>Error al listar directorio padre:</strong></p>
                <div class="callout-error">
                    Access denied - path outside allowed directories: C:\\Users\\eutiz\\Downloads not in C:\\Users\\eutiz\\Downloads\\practica1_mcp
                </div>

                <p style="font-size: 0.85em; color: var(--muted-text); margin-top: 15px;">
                    * <strong>Análisis:</strong> La restricción la impone de forma estricta el propio <strong>servidor MCP</strong> (no el modelo ni el host).
                </p>
            </div>
        </div>
    </div>

    <!-- FASE D -->
    <div class="section-title">Fase D — Servidor de Memoria (memory)</div>
    <div class="card">
        <p><strong>Servidor:</strong> <code>@modelcontextprotocol/server-memory (v2.1.1)</code></p>
        <p><strong>Grafo de Conocimiento Almacenado:</strong></p>
        <pre style="background: #181820; padding: 12px; border-radius: 4px; border: 1px solid var(--border-color); color: var(--green-accent);">
{{ memory_data | tojson(indent=2) }}
        </pre>
    </div>

</body>
</html>
"""

@app.route('/')
def index():
    calificaciones, avg_group, passed, failed = get_fase_a_data()
    entidades = get_fase_b_data()
    memory_data = get_fase_d_data()
    return render_template_string(
        HTML_TEMPLATE,
        calificaciones=calificaciones,
        avg_group=avg_group,
        passed=passed,
        failed=failed,
        entidades=entidades,
        memory_data=memory_data
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)