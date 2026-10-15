import copy
import json
from pathlib import Path

import pytest

from src.historia import HistoriaInvalida, cargar_historia, construir_historia, validar
from src.motor import OpcionNoDisponible, Sesion

DATA = Path(__file__).resolve().parent.parent / "data"
ORIGINAL = DATA / "la_ultima_transmision.json"
FARO = DATA / "historia_faro.json"


def datos_originales():
    return json.loads(ORIGINAL.read_text(encoding="utf-8"))


def sesion_en_e3(conoce):
    s = Sesion(cargar_historia(ORIGINAL))
    s.elegir("revisar")
    s.elegir("investigar" if conoce else "continuar")
    return s


def ids(s):
    return [o.id for o in s.opciones_disponibles()]


# U1: condiciones cumplidas / no cumplidas habilitan solo las opciones correspondientes
@pytest.mark.parametrize("conoce,esperadas", [
    (True, ["activar_codigo", "cortar"]),
    (False, ["activar_sin_verificar", "cortar"]),
])
def test_u1_condiciones_habilitan_opciones(conoce, esperadas):
    assert ids(sesion_en_e3(conoce)) == esperadas


# U2: elección válida aplica efectos y avanza al destino correcto
@pytest.mark.parametrize("conoce,opcion,destino,variables", [
    (True, "activar_codigo", "E4", {"conoce_origen": True, "confia_en_la_voz": True}),
    (False, "activar_sin_verificar", "E5", {"conoce_origen": False, "confia_en_la_voz": True}),
    (True, "cortar", "E6", {"conoce_origen": True, "confia_en_la_voz": False}),
    (False, "cortar", "E6", {"conoce_origen": False, "confia_en_la_voz": False}),
])
def test_u2_eleccion_valida(conoce, opcion, destino, variables):
    s = sesion_en_e3(conoce)
    s.elegir(opcion)
    assert s.escena.id == destino
    assert s.variables == variables


# U3: opción inexistente o no habilitada deja intacto el estado (CA02)
@pytest.mark.parametrize("conoce,opcion", [
    (False, "activar_codigo"),   # no habilitada
    (True, "activar_sin_verificar"),  # no habilitada
    (True, "no_existe"),         # inexistente
])
def test_u3_opcion_invalida_no_altera_estado(conoce, opcion):
    s = sesion_en_e3(conoce)
    antes = (s.escena.id, s.variables)
    with pytest.raises(OpcionNoDisponible):
        s.elegir(opcion)
    assert (s.escena.id, s.variables) == antes


# U4: errores de contenido producen rechazo controlado con causa e ID
def _mutar(f):
    d = datos_originales()
    f(d)
    return d


VARIANTES_INVALIDAS = [
    ("falta_titulo", _mutar(lambda d: d.pop("titulo")), "titulo"),
    ("falta_escenas", _mutar(lambda d: d.pop("escenas")), "escenas"),
    ("falta_campo_escena", _mutar(lambda d: d["escenas"][0].pop("texto")), "texto"),
    ("falta_campo_opcion", _mutar(lambda d: d["escenas"][0]["opciones"][0].pop("destino")), "destino"),
    ("inicio_inexistente", _mutar(lambda d: d.update(inicio="X9")), "X9"),
    ("escena_duplicada", _mutar(lambda d: d["escenas"].append(copy.deepcopy(d["escenas"][0]))), "repetido"),
    ("opcion_duplicada", _mutar(lambda d: d["escenas"][1]["opciones"].append(copy.deepcopy(d["escenas"][1]["opciones"][0]))), "investigar"),
    ("destino_inexistente", _mutar(lambda d: d["escenas"][0]["opciones"][0].update(destino="E99")), "E99"),
    ("variable_no_declarada_condicion", _mutar(lambda d: d["escenas"][2]["opciones"][0]["condiciones"].update(fantasma=True)), "fantasma"),
    ("variable_no_declarada_efecto", _mutar(lambda d: d["escenas"][1]["opciones"][0]["efectos"].update(fantasma=True)), "fantasma"),
    ("valor_no_booleano_condicion", _mutar(lambda d: d["escenas"][2]["opciones"][0]["condiciones"].update(conoce_origen="si")), "no booleano"),
    ("valor_no_booleano_efecto", _mutar(lambda d: d["escenas"][1]["opciones"][0]["efectos"].update(conoce_origen=1)), "no booleano"),
    ("valor_no_booleano_inicial", _mutar(lambda d: d["variables"].update(conoce_origen=0)), "no booleano"),
    ("final_con_opciones", _mutar(lambda d: d["escenas"][3].update(opciones=[copy.deepcopy(d["escenas"][0]["opciones"][0])])), "E4"),
    ("no_final_sin_opciones", _mutar(lambda d: d["escenas"][0].update(opciones=[])), "E1"),
    ("estructura_incorrecta_raiz", [1, 2, 3], "objeto"),
]


@pytest.mark.parametrize("nombre,datos,fragmento", VARIANTES_INVALIDAS, ids=[v[0] for v in VARIANTES_INVALIDAS])
def test_u4_errores_de_contenido(nombre, datos, fragmento):
    errores = validar(datos)
    assert errores, f"{nombre}: debía producir al menos un error"
    assert any(fragmento in e for e in errores), f"{nombre}: ningún mensaje menciona '{fragmento}': {errores}"
    with pytest.raises(HistoriaInvalida):
        construir_historia(datos)


def test_u4_archivo_ilegible(tmp_path):
    roto = tmp_path / "roto.json"
    roto.write_text('{"titulo": ', encoding="utf-8")
    with pytest.raises(HistoriaInvalida) as exc:
        cargar_historia(roto)
    assert "ilegible" in exc.value.errores[0]


def test_u4_archivo_inexistente(tmp_path):
    with pytest.raises(HistoriaInvalida):
        cargar_historia(tmp_path / "nada.json")


# CA03: destino E99 rechazado, sin sesión jugable
def test_ca03_destino_inexistente_en_archivo():
    with pytest.raises(HistoriaInvalida) as exc:
        cargar_historia(DATA / "invalidas" / "destino_inexistente.json")
    assert any("E99" in e for e in exc.value.errores)


# U5: reiniciar restaura escena y variables iniciales
def test_u5_reiniciar():
    s = sesion_en_e3(True)
    s.elegir("activar_codigo")
    assert s.es_final()
    s.reiniciar()
    assert s.escena.id == "E1"
    assert s.variables == {"conoce_origen": False, "confia_en_la_voz": False}
    assert not s.es_final()


# Escena no final sin opciones habilitadas durante la partida
def test_escena_bloqueada_se_informa_y_permite_reiniciar():
    d = {
        "titulo": "Bloqueo", "inicio": "A", "variables": {"x": False},
        "escenas": [
            {"id": "A", "texto": "a", "final": False, "opciones": [
                {"id": "o", "texto": "o", "destino": "B", "condiciones": {"x": True}, "efectos": {}}]},
            {"id": "B", "texto": "b", "final": True, "opciones": []},
        ],
    }
    s = Sesion(construir_historia(d))
    assert s.bloqueada()
    assert s.opciones_disponibles() == []
    s.reiniciar()
    assert s.escena.id == "A"


# CA01
def test_ca01_revisar_e_investigar():
    s = Sesion(cargar_historia(ORIGINAL))
    s.elegir("revisar")
    s.elegir("investigar")
    assert s.escena.id == "E3"
    assert s.variables["conoce_origen"] is True
    assert ids(s) == ["activar_codigo", "cortar"]


# I1: archivo real + motor, hasta alcanzar cada final
@pytest.mark.parametrize("ruta,decisiones,final", [
    (ORIGINAL, ["revisar", "investigar", "activar_codigo"], "E4"),
    (ORIGINAL, ["revisar", "continuar", "activar_sin_verificar"], "E5"),
    (ORIGINAL, ["revisar", "continuar", "cortar"], "E6"),
])
def test_i1_integracion_tres_finales(ruta, decisiones, final):
    s = Sesion(cargar_historia(ruta))
    for d in decisiones:
        assert not s.es_final()
        s.elegir(d)
    assert s.es_final()
    assert s.escena.id == final


# Segunda historia con el mismo motor, sin cambios en el código
@pytest.mark.parametrize("decisiones,final", [
    (["buscar", "abrir"], "F3"),
    (["directo", "forzar"], "F4"),
])
def test_segunda_historia_mismo_motor(decisiones, final):
    s = Sesion(cargar_historia(FARO))
    for d in decisiones:
        s.elegir(d)
    assert s.es_final() and s.escena.id == final
