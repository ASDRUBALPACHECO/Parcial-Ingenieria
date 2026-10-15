"""Contenido: modelo de datos de una historia y su validación.

No contiene reglas de juego ni entrada/salida de usuario.
"""
import json
from dataclasses import dataclass


class HistoriaInvalida(Exception):
    """El archivo de historia no es válido. `errores` lista todas las causas."""

    def __init__(self, errores):
        self.errores = list(errores)
        super().__init__("\n".join(self.errores))


@dataclass(frozen=True)
class Opcion:
    id: str
    texto: str
    destino: str
    condiciones: dict
    efectos: dict


@dataclass(frozen=True)
class Escena:
    id: str
    texto: str
    final: bool
    opciones: tuple


@dataclass(frozen=True)
class Historia:
    titulo: str
    inicio: str
    variables: dict
    escenas: dict  # id -> Escena


def _es_texto(v):
    return isinstance(v, str) and v != ""


def _validar_mapa_booleano(mapa, declaradas, ubicacion, errores):
    if not isinstance(mapa, dict):
        errores.append(f"{ubicacion}: debe ser un mapa de variable a booleano")
        return
    for var, val in mapa.items():
        if var not in declaradas:
            errores.append(f"{ubicacion}: variable no declarada '{var}'")
        if not isinstance(val, bool):
            errores.append(f"{ubicacion}: valor no booleano para '{var}' ({val!r})")


def validar(datos):
    """Devuelve la lista de errores de contenido (vacía si es válido)."""
    errores = []
    if not isinstance(datos, dict):
        return ["La historia debe ser un objeto JSON en la raíz"]

    for campo, tipo in (("titulo", str), ("inicio", str), ("variables", dict), ("escenas", list)):
        if campo not in datos:
            errores.append(f"Falta el campo obligatorio '{campo}'")
        elif not isinstance(datos[campo], tipo):
            errores.append(f"El campo '{campo}' tiene un tipo incorrecto")

    variables = datos.get("variables") if isinstance(datos.get("variables"), dict) else {}
    for var, val in variables.items():
        if not isinstance(val, bool):
            errores.append(f"variables.{var}: valor inicial no booleano ({val!r})")

    escenas = datos.get("escenas") if isinstance(datos.get("escenas"), list) else []
    if "escenas" in datos and isinstance(datos["escenas"], list) and not escenas:
        errores.append("El campo 'escenas' no puede estar vacío")

    # Pasada 1: estructura y IDs de escenas
    ids = []
    for i, esc in enumerate(escenas):
        if not isinstance(esc, dict):
            errores.append(f"escenas[{i}]: debe ser un objeto")
            continue
        for campo in ("id", "texto", "final", "opciones"):
            if campo not in esc:
                errores.append(f"escenas[{i}]: falta el campo obligatorio '{campo}'")
        if "id" in esc:
            if not _es_texto(esc["id"]):
                errores.append(f"escenas[{i}].id: debe ser un texto no vacío")
            elif esc["id"] in ids:
                errores.append(f"ID de escena repetido: '{esc['id']}'")
            else:
                ids.append(esc["id"])

    if isinstance(datos.get("inicio"), str) and datos["inicio"] not in ids:
        errores.append(f"La escena inicial '{datos['inicio']}' no existe")

    # Pasada 2: contenido de cada escena y opción
    for i, esc in enumerate(escenas):
        if not isinstance(esc, dict):
            continue
        eid = esc.get("id", f"escenas[{i}]")
        if "texto" in esc and not isinstance(esc["texto"], str):
            errores.append(f"Escena {eid}: 'texto' debe ser texto")
        if "final" in esc and not isinstance(esc["final"], bool):
            errores.append(f"Escena {eid}: 'final' debe ser booleano")
        ops = esc.get("opciones")
        if "opciones" in esc and not isinstance(ops, list):
            errores.append(f"Escena {eid}: 'opciones' debe ser una lista")
            continue
        if isinstance(ops, list) and isinstance(esc.get("final"), bool):
            if esc["final"] and len(ops) != 0:
                errores.append(f"Escena final {eid}: debe tener cero opciones (tiene {len(ops)})")
            if not esc["final"] and len(ops) == 0:
                errores.append(f"Escena no final {eid}: debe tener al menos una opción")
        ids_op = []
        for j, op in enumerate(ops or []):
            if not isinstance(op, dict):
                errores.append(f"Escena {eid}, opciones[{j}]: debe ser un objeto")
                continue
            for campo in ("id", "texto", "destino"):
                if campo not in op:
                    errores.append(f"Escena {eid}, opciones[{j}]: falta el campo obligatorio '{campo}'")
            oid = op.get("id", f"opciones[{j}]")
            if "id" in op:
                if op["id"] in ids_op:
                    errores.append(f"ID de opción repetido en escena {eid}: '{op['id']}'")
                ids_op.append(op["id"])
            if "destino" in op and op["destino"] not in ids:
                errores.append(f"Opción {eid}/{oid}: destino inexistente '{op['destino']}'")
            _validar_mapa_booleano(op.get("condiciones", {}), variables,
                                   f"Opción {eid}/{oid}, condiciones", errores)
            _validar_mapa_booleano(op.get("efectos", {}), variables,
                                   f"Opción {eid}/{oid}, efectos", errores)
    return errores


def construir_historia(datos):
    """Valida y construye una Historia; lanza HistoriaInvalida si hay errores."""
    errores = validar(datos)
    if errores:
        raise HistoriaInvalida(errores)
    escenas = {}
    for e in datos["escenas"]:
        opciones = tuple(
            Opcion(o["id"], o["texto"], o["destino"],
                   dict(o.get("condiciones", {})), dict(o.get("efectos", {})))
            for o in e["opciones"]
        )
        escenas[e["id"]] = Escena(e["id"], e["texto"], e["final"], opciones)
    return Historia(datos["titulo"], datos["inicio"], dict(datos["variables"]), escenas)


def cargar_historia(ruta):
    """Lee un archivo JSON y devuelve la Historia validada."""
    try:
        with open(ruta, encoding="utf-8") as f:
            datos = json.load(f)
    except FileNotFoundError:
        raise HistoriaInvalida([f"No se encontró el archivo '{ruta}'"])
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HistoriaInvalida([f"Archivo ilegible o JSON mal formado ('{ruta}'): {exc}"])
    return construir_historia(datos)
