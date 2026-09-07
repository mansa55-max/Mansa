from .. import config


class ScriptWriterError(Exception):
    pass


class ScriptWriterNotConfiguredError(ScriptWriterError):
    pass


def generate_script(product_name: str, product_description: str) -> str:
    if not config.ANTHROPIC_API_KEY:
        raise ScriptWriterNotConfiguredError(
            "ANTHROPIC_API_KEY manquant. Ajoute-le dans le fichier .env pour générer un script automatiquement, "
            "ou écris ton propre script."
        )
    try:
        import anthropic
    except ImportError as exc:
        raise ScriptWriterError("La bibliothèque anthropic n'est pas installée.") from exc

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    prompt = (
        f"Écris un script publicitaire UGC (User Generated Content) pour le produit \"{product_name}\".\n"
        f"Description du produit : {product_description}\n\n"
        "Contraintes :\n"
        "- À la première personne, comme une vraie personne qui recommande le produit à un(e) ami(e), ton "
        "casual et authentique, pas publicitaire/corporate.\n"
        "- Environ 40 à 70 mots (15 à 25 secondes de parole).\n"
        "- Pas de titre, pas de guillemets, pas de didascalies : uniquement le texte parlé, prêt à être lu à voix haute.\n"
        "- En français."
    )
    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    script = "".join(block.text for block in message.content if hasattr(block, "text")).strip()
    if not script:
        raise ScriptWriterError("Claude n'a renvoyé aucun texte.")
    return script
