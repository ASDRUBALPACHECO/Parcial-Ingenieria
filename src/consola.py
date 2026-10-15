"""Interfaz de consola. Uso: python -m src.consola data/la_ultima_transmision.json"""
import sys

from .historia import HistoriaInvalida, cargar_historia
from .motor import OpcionNoDisponible, Sesion


def jugar(historia, entrada=input, salida=print):
    sesion = Sesion(historia)
    salida(f"=== {historia.titulo} ===")
    while True:
        salida(f"\n[{sesion.escena.id}] {sesion.escena.texto}")
        if sesion.es_final():
            salida("\n-- FIN --")
            if entrada("¿Jugar de nuevo? (s/n): ").strip().lower() == "s":
                sesion.reiniciar()
                continue
            return
        opciones = sesion.opciones_disponibles()
        if not opciones:
            salida("La historia quedó bloqueada: no hay opciones disponibles.")
            if entrada("¿Reiniciar? (s/n): ").strip().lower() == "s":
                sesion.reiniciar()
                continue
            return
        for n, op in enumerate(opciones, 1):
            salida(f"  {n}. {op.texto}")
        texto = entrada("Elige una opción: ").strip()
        if not texto.isdigit() or not 1 <= int(texto) <= len(opciones):
            salida("Entrada no válida. Escribe el número de una opción.")
            continue
        try:
            sesion.elegir(opciones[int(texto) - 1].id)
        except OpcionNoDisponible as exc:  # no debería ocurrir; defensa
            salida(str(exc))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("Uso: python -m src.consola <archivo_historia.json>")
        return 2
    try:
        historia = cargar_historia(argv[0])
    except HistoriaInvalida as exc:
        print("No se puede jugar: la historia contiene errores.")
        for err in exc.errores:
            print(f" - {err}")
        return 1
    try:
        jugar(historia)
    except (EOFError, KeyboardInterrupt):
        print("\nSesión terminada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
