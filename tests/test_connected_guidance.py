from escala_server.connected_guidance import anonymize_preview, capabilities, recommend, swt_recipe, record_decision


def test_guidance_never_guesses_host_or_requires_connection():
    none = recommend("documents", capabilities("none"))
    assert none.connector is None
    assert "no instalará" in none.host_message
    drive = recommend("documents", capabilities("codex", {"drive": True}))
    assert drive.connector == "Drive"
    assert "fuera de ScaleUp" in drive.host_message


def test_anonymization_rejects_secrets_and_minimizes_sensitive_content():
    assert anonymize_preview("api_key=abc") is None
    preview = anonymize_preview("cliente Aurora escribió a ana@lumen.mx por MXN 125,000; folio 123456789")
    assert preview is not None
    assert "ana@lumen.mx" not in preview and "125,000" not in preview and "123456789" not in preview
    assert "[PERSONA]" in preview and "[IMPORTE]" in preview and "[IDENTIFICADOR]" in preview


def test_swt_recipe_is_editable_and_not_a_scheduled_task():
    recipe = swt_recipe(capabilities("claude", {"deep_research": False}), months=6)
    assert "6 meses" in recipe.purpose
    assert recipe.connector is None
    assert "no programa una tarea" in recipe.host_message


def test_connected_guidance_conversation_never_connects_or_stores_secret(tmp_path):
    from coaching.router.conversation import run

    root = tmp_path / "guide"
    root.mkdir()
    answer = run("quiero conectar drive para revisar documentos", base_path=root)
    assert "no instalará" in answer and "alternativa local" in answer.lower()
    accepted = run("acepto", base_path=root)
    assert "registrada localmente" in accepted and "No conecté" in accepted
    preview = run("drive datos: cliente Aurora escribió a ana@lumen.mx por MXN 120,000", base_path=root)
    assert "ana@lumen.mx" not in preview and "[PERSONA]" in preview
    stopped = run("drive datos: api_key=supersecret", base_path=root)
    assert "no lo guardaré" in stopped.lower()


def test_explicit_decision_records_no_external_content(tmp_path):
    assert not record_decision(str(tmp_path), need="documents", state="accepted", explicit_confirmation=False)
    assert record_decision(str(tmp_path), need="documents", state="rejected", explicit_confirmation=True)
    import sqlite3
    from escala_server.project_memory import ProjectMemoryRuntime
    with sqlite3.connect(ProjectMemoryRuntime(tmp_path).db_path) as db:
        value = db.execute("SELECT value FROM memory_facts WHERE key LIKE 'connected_guidance.decision.%'").fetchone()[0]
    assert 'external_content' in value and 'token' not in value
