# pyright: strict
"""Owner-facing text of the journey (plain Spanish, one question per message).

Never say "journey", "embudo" or a procedure name to the owner: the journey is
"cómo llega un cliente hasta que te compra".
"""

from __future__ import annotations

ASK_NEW = (
    "Para ver dónde se te van los clientes, ¿me cuentas cómo llega un cliente "
    "hasta que te compra? Son 5 pasos y unos 5 minutos. Si prefieres, lo vemos "
    "después."
)

ASK_UPDATE = (
    "Lo que me contaste de cómo llega un cliente hasta que te compra ya tiene "
    "tiempo. ¿Lo revisamos para ver qué cambió? Son 5 pasos y unos 5 minutos. "
    "Si prefieres, lo vemos después."
)
