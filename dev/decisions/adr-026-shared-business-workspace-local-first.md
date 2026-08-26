# ADR-026: Workspace empresarial compartido con estado SQLite local

**Estado:** Aprobada para E26
**Fecha:** 2026-08-26

## Contexto

E22 puso la memoria empresarial en SQLite bajo la raíz de cada proyecto. Esa
ubicación es segura para una persona, pero no para una carpeta que Drive
Desktop, Dropbox, OneDrive o un sistema corporativo sincroniza entre varios
equipos: SQLite, WAL, SHM, locks y backups no son documentos colaborativos y
pueden divergir o corromperse.

La alternativa de una base cloud, PostgreSQL, API propia u OAuth añade una
operación desproporcionada para un empresario no técnico y contradice el
principio local-first de ScaleUp.

## Decisión

1. Un workspace compartido se identifica por `scaleup-workspace.yaml` y contiene
   sólo documentos empresariales humanos: Markdown/YAML en `company`, `areas`,
   `plans`, `cadence`, `decisions` y `contributions`.
2. Cada computadora crea su propio estado en
   `{local_state_root}/{workspace_id}/escala.db`, fuera del workspace. Se
   prohíben ahí SQLite, WAL, SHM, locks y backups.
3. SQLite es un índice desechable y local: registra hashes, procedencia y hechos
   confirmados; se reconstruye de forma determinística desde los documentos.
4. Una contribución es append-only, lleva UUID, área, autor, rol, fuente,
   fecha, estado y, cuando aplique, hash de la versión que conocía. No reemplaza
   un documento canónico.
5. Los documentos canónicos exigen propietario y estado `confirmed`. Una
   conciliación sólo ocurre con confirmación humana explícita, conserva el
   documento anterior y las contribuciones resueltas en un registro versionado.
6. Drive/Dropbox/OneDrive siguen controlando acceso y sincronización. ScaleUp no
   promete RBAC, OAuth ni conectividad nativa.
7. Secretos y valores que parezcan credenciales se rechazan antes de escribirse
   o indexarse en el workspace.

## Migración de E22

Al abrir por primera vez un workspace que contiene la base E22 heredada,
ScaleUp usa el API de backup de SQLite para crear una copia consistente en el
estado local, valida el esquema, genera una copia de seguridad local y sólo
después retira los artefactos SQLite conocidos de la carpeta compartida. Si el
paso no puede verificarse, no usa la carpeta compartida como fallback.

## Consecuencias

- Cada colaborador puede trabajar offline; los índices convergen cuando el
  proveedor sincroniza documentos.
- La pérdida de una base local no pierde conocimiento confirmado.
- Un nuevo colaborador no necesita historial de chat ni acceso a otra máquina.
- Los conflictos de archivos se muestran y se conservan; no se resuelven con
  “última escritura gana”.
- El agente guía el flujo con la única skill pública y no pide comandos al
  empresario.

## Alternativas descartadas

| Alternativa | Motivo |
|---|---|
| Sincronizar `escala.db` con Drive | WAL, locks y copias en conflicto lo hacen inseguro. |
| PostgreSQL + API multiusuario | Añade servidor, operaciones, autenticación y costo fuera del valor inicial. |
| OAuth directo con Drive | Traslada permisos, retención y soporte al producto sin necesidad. |
| Compartir sólo chats | No es portable, auditable ni independiente del proveedor de modelo. |
| Sobrescribir canónicos con contribuciones | Borra contexto y atribución de otros colaboradores. |

## Verificación

- Dos estados locales construidos desde la misma instantánea producen el mismo
  digest e inventario confirmado.
- La migración E22 elimina SQLite del workspace únicamente después de conservar
  una copia local validada.
- Un cambio basado en un hash antiguo exige conciliación y conserva versiones.
- La skill pública prepara y revisa el workspace en lenguaje natural.
- El instalador distribuye el runtime completo y la suite cubre aislamiento,
  migración, reconstrucción, privacidad, conversación e instalación.
