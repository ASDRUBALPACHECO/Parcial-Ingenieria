# La última transmisión — motor de historias interactivas

**Integrantes:** Joseph Antony Torres · Asdrúbal Pacheco Rubio (completar nombres completos)
**Docente:** Aisner José Marrugo Juliao · **Materia:** Ingeniería de Software

## Requisitos
- Python 3.10 o superior
- pytest (solo para las pruebas): `pip install -r requirements.txt`
- Licencias: Python (PSF), pytest (MIT)

## Ejecutar
```
python -m src.consola data/la_ultima_transmision.json
python -m src.consola data/historia_faro.json          # segunda historia, mismo motor
python -m src.consola data/invalidas/destino_inexistente.json   # muestra el rechazo (CA03)
```

## Pruebas
```
python -m pytest -v
```
El registro de la última ejecución está en `evidencia/resultados_pruebas.txt`.

## Estructura
- `src/historia.py` — contenido: modelo de datos y validación del archivo
- `src/motor.py` — reglas: sesión, condiciones, efectos, reinicio y deshacer
- `src/consola.py` — interfaz de consola
- `data/` — historias (`la_ultima_transmision.json`, `historia_faro.json`) y ejemplos inválidos en `data/invalidas/`
- `tests/test_motor.py` — pruebas U1–U5, I1 y validación

## Formato de contenido (JSON)
Historia: `titulo`, `inicio` (ID de escena), `variables` (mapa de booleanos), `escenas`.
Escena: `id`, `texto`, `final`, `opciones` (vacía si es final).
Opción: `id` (único en la escena), `texto`, `destino`, `condiciones` (mapa de igualdades, opcional), `efectos` (mapa de asignaciones, opcional).
Un mapa de condiciones vacío o ausente habilita la opción; todas las condiciones deben cumplirse. Solo se admiten valores booleanos.

## Rutas para demostrar cada final (historia principal)
- E4 Rescate: `revisar` → `investigar` → `activar_codigo`
- E5 El eco: `revisar` → `continuar` → `activar_sin_verificar`
- E6 Silencio: `revisar` → (`investigar` o `continuar`) → `cortar`

## Conflicto retroceso (escritora) vs. irreversibilidad (diseñador)
- **v1 (hora 6):** no se implementó retroceso. Acuerdo provisional: decisiones irreversibles, con la pregunta de aclaración *¿el retroceso debe estar siempre disponible o solo en ciertas escenas?*
- **v2 (solicitud de cambio):** el cliente decidió que el lector puede deshacer su última decisión. Reglas implementadas:
  - restaura exactamente escena y variables anteriores a la última elección válida;
  - un solo nivel: tras deshacer no hay otro retroceso hasta una nueva elección válida;
  - al comenzar o reiniciar no hay retroceso (el reinicio elimina el historial);
  - una opción inexistente o no habilitada no modifica la sesión ni el historial;
  - se puede deshacer desde un final (E4, E5, E6 regresan a E3).
- En la consola: opción `0` para deshacer (o `d` en la pantalla de final).

## Limitaciones conocidas
- No se analizan automáticamente todos los caminos posibles del relato (alcanzabilidad); un bloqueo se informa en la partida.
- Sin guardado entre ejecuciones.
