"""Reglas: sesión de juego. Evalúa condiciones y aplica efectos desde los datos.

No conoce identificadores de ninguna historia concreta ni hace entrada/salida.
"""


class OpcionNoDisponible(Exception):
    """La opción no existe o no está habilitada en la escena actual."""


class Sesion:
    def __init__(self, historia):
        self._historia = historia
        self.reiniciar()

    def reiniciar(self):
        self._escena = self._historia.inicio
        self._variables = dict(self._historia.variables)

    @property
    def escena(self):
        return self._historia.escenas[self._escena]

    @property
    def variables(self):
        return dict(self._variables)

    def es_final(self):
        return self.escena.final

    def opciones_disponibles(self):
        return [
            op for op in self.escena.opciones
            if all(self._variables[k] == v for k, v in op.condiciones.items())
        ]

    def bloqueada(self):
        """Escena no final sin ninguna opción habilitada."""
        return not self.es_final() and not self.opciones_disponibles()

    def elegir(self, id_opcion):
        for op in self.opciones_disponibles():
            if op.id == id_opcion:
                self._variables.update(op.efectos)
                self._escena = op.destino
                return self.escena
        raise OpcionNoDisponible(
            f"La opción '{id_opcion}' no existe o no está habilitada en la escena {self._escena}"
        )
