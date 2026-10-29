"""Local assistant responses that do not use an LLM or modify stored data."""

import re
import sqlite3
import unicodedata
from contextlib import closing
from pathlib import Path

from app.config import BASE_DIR, settings

FAQ_PATH = BASE_DIR / "data" / "faq.md"

_TOPICS = {
    "shipping": ("shipping", "delivery", "livraison", "expédition", "expedier"),
    "returns": ("return", "returns", "refund", "retour", "rembours"),
    "warranty": ("warranty", "garantie"),
    "payment": ("payment", "payer", "paiement", "paiements", "installment", "carte"),
    "contact": ("contact", "support", "email", "phone", "telephone", "téléphone"),
}
_PRODUCT_WORDS = (
    "product", "products", "laptop", "ordinateur", "price", "cheapest", "cheap",
    "stock", "brand", "product", "produit", "produits", "prix", "moins cher",
    "marque", "brand", "category", "catégorie", "categorie", "nom", "chercher",
    "cherche", "recherche", "trouve", "trouver", "search", "find", "disponible",
    "casque", "telephone", "téléphone", "ecouteur", "écouteur", "montre",
    "tablette", "moins de",
)
_STOP_WORDS = {
    "the", "what", "which", "have", "with", "show", "find", "cheapest", "cheap",
    "price", "prices", "product", "products", "do", "you", "your", "is", "are",
    "a", "an", "of", "for", "me", "please", "les", "des", "une", "un", "quel",
    "quelle", "quels", "quelles", "cherche", "trouve", "produit", "produits",
    "prix", "moins", "cher", "chère", "marque", "brand", "category", "catégorie",
    "categorie", "nom", "par", "dans", "pour", "sur", "stock", "disponible",
    "disponibles", "recherche", "chercher", "trouver", "find", "search", "sont",
    "coutent", "cost", "dinars", "dinar", "dt", "dont", "est", "affiche",
    "afficher", "articles", "article", "maximum", "maximal", "maximale",
    "as-tu", "avez-vous", "est-ce", "avez", "vous", "moi", "got",
    "montre-moi",
}

_MAX_PRICE_PATTERNS = (
    re.compile(
        r"\b(?:moins\s+de|under|below|less\s+than|at\s+most|up\s+to|au\s+plus|"
        r"jusqu['’]?\s+a|inferieur(?:e)?\s+a)\s*[$€£]?\s*"
        r"(\d+(?:[.,]\d{1,2})?)\s*(?:dinars?|dt|dollars?|usd|euros?|eur)?\b"
    ),
    re.compile(
        r"\b(?:prix\s+(?:maximum|maximal|maximale|max)|maximum(?:\s+price)?|"
        r"max(?:imum)?(?:\s+price)?)\s*(?:(?:de|of)\s+)?[$€£]?\s*"
        r"(\d+(?:[.,]\d{1,2})?)\s*(?:dinars?|dt|dollars?|usd|euros?|eur)?\b"
    ),
)

_CATEGORY_SYNONYMS = {
    "ordinateur": ("laptop", "laptops"),
    "portable": ("laptop", "laptops"),
    "telephone": ("smartphone", "smartphones"),
    "ecouteur": ("audio", "headphone", "headphones"),
    "casque": ("audio", "headphone", "headphones"),
    "headphone": ("audio",),
    "headphones": ("audio",),
    "montre": ("smartwatch", "smartwatches"),
    "tablette": ("tablet", "tablets"),
}

_AVAILABILITY_PATTERN = re.compile(
    r"\b(?:as\s*-?\s*tu|avez\s*-?\s*vous|est\s*-?\s*ce\s+que|"
    r"disponible|disponibles|available|in\s+stock|en\s+stock)\b"
)


def _normalize(text: str) -> str:
    """Fold accents and case so French paraphrases match consistently."""
    folded = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in folded if not unicodedata.combining(char))


def _faq_section(question: str) -> str | None:
    """Return French answers using only facts present in the local FAQ."""
    if not FAQ_PATH.is_file():
        return None
    normalized = _normalize(question)
    shipping_terms = (
        "shipping", "delivery", "livraison", "livrer", "livree", "arrive",
        "commande", "expedition", "expedier",
    )
    if any(term in normalized for term in shipping_terms):
        asks_express = "express" in normalized
        asks_price = any(term in normalized for term in ("combien", "cout", "prix", "tarif", "cost", "how much"))
        asks_time = any(term in normalized for term in ("combien de jours", "delai", "jour", "quand", "arrive", "takes", "long"))
        asks_standard = any(term in normalized for term in ("standard", "normale", "normal", "gratuite", "gratuit"))

        if asks_express and asks_price:
            return "La livraison express (le lendemain) coûte 15 dinars."
        if asks_express and asks_time:
            return "La livraison express est disponible le lendemain et coûte 15 dinars."
        if asks_standard and (asks_price or "gratuit" in normalized):
            return (
                "La livraison standard est gratuite pour les commandes de plus de 200 dinars. "
                "La FAQ ne précise pas son tarif pour les commandes de 200 dinars ou moins."
            )
        if asks_time:
            return (
                "La livraison standard prend 2 à 4 jours ouvrés. "
                "La livraison express est disponible le lendemain pour 15 dinars."
            )
        if asks_express:
            return "La livraison express est disponible le lendemain pour 15 dinars."
        return (
            "La livraison standard est gratuite pour les commandes de plus de 200 dinars et prend "
            "2 à 4 jours ouvrés. La livraison express est disponible le lendemain pour 15 dinars."
        )

    if any(term in normalized for term in ("return", "refund", "retour", "rembours")):
        return (
            "Vous pouvez retourner un produit dans les 14 jours suivant l’achat, dans sa boîte d’origine "
            "avec le reçu. Le remboursement est effectué sur le moyen de paiement initial sous 5 jours ouvrés. "
            "Les logiciels ouverts et les écouteurs ne sont pas repris pour des raisons d’hygiène."
        )
    if any(term in normalized for term in ("warranty", "garantie")):
        return (
            "Les produits neufs ont une garantie fabricant de 12 mois. Les produits reconditionnés ont "
            "une garantie TechStore de 6 mois. Une extension de garantie peut être achetée dans les 30 jours suivant l’achat."
        )
    if any(term in normalized for term in ("payment", "payer", "paiement", "installment", "carte", "espece", "cash")):
        return "La boutique accepte les espèces et les cartes bancaires. Le paiement en 3 fois est proposé pour les achats de plus de 900 dinars."
    if any(
        term in normalized
        for term in ("contact", "support", "email", "numero", "number", "call")
    ) or re.search(r"\bphone\b", normalized):
        return "Vous pouvez contacter le support à support@techstore.tn ou au 71 234 567, du lundi au samedi, de 9 h à 19 h."
    return None


def _extract_max_price(question: str) -> tuple[float | None, str]:
    """Extract an explicit upper price bound and return the remaining text."""
    normalized = _normalize(question)
    for pattern in _MAX_PRICE_PATTERNS:
        match = pattern.search(normalized)
        if match:
            raw_price = match.group(1).replace(",", ".")
            remaining = f"{normalized[:match.start()]} {normalized[match.end():]}"
            return float(raw_price), remaining
    return None, normalized


def _has_availability_intent(question: str) -> bool:
    return bool(_AVAILABILITY_PATTERN.search(_normalize(question)))


def _mentions_catalog_identifier(question: str) -> bool:
    """Check whether a question mentions an identifier in the local catalog."""
    db_path = Path(settings.db_path)
    if not db_path.is_file() or db_path.stat().st_size == 0:
        return False

    question_terms = set(re.findall(r"[\w-]+", _normalize(question), flags=re.UNICODE))
    ignored = _STOP_WORDS | {"fictif", "fictive", "demo", "demonstration"}
    try:
        with closing(sqlite3.connect(f"{db_path.as_uri()}?mode=ro", uri=True)) as connection:
            rows = connection.execute(
                "SELECT p.name, c.name, b.name FROM products p "
                "LEFT JOIN categories c ON c.id = p.category_id "
                "LEFT JOIN brands b ON b.id = p.brand_id"
            ).fetchall()
    except sqlite3.Error:
        return False

    for row in rows:
        for value in row:
            if not value:
                continue
            identifier_terms = {
                token
                for token in re.findall(r"[\w-]+", _normalize(value), flags=re.UNICODE)
                if len(token) > 3 and token not in ignored
            }
            if question_terms & identifier_terms:
                return True
    return False


def _local_product_search(question: str) -> str:
    db_path = Path(settings.db_path)
    if not db_path.is_file() or db_path.stat().st_size == 0:
        return (
            "La base locale ne contient pas encore de produits. "
            "Les réponses sur les politiques de la boutique restent disponibles ici."
        )

    try:
        with closing(
            sqlite3.connect(f"{db_path.as_uri()}?mode=ro", uri=True)
        ) as connection, connection:
            connection.row_factory = sqlite3.Row
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            if "products" not in tables:
                return "La base locale ne contient pas encore de table produits."

            max_price, searchable_text = _extract_max_price(question)
            tokens = [
                token
                for token in re.findall(r"[\w-]+", searchable_text, flags=re.UNICODE)
                if len(token) > 2 and token not in _STOP_WORDS
            ]
            conditions = []
            parameters: list[object] = []
            if tokens:
                parts = []
                for token in tokens:
                    # Support common French/English plural suffixes in questions
                    # when the catalog stores the corresponding singular form.
                    variants = [token]
                    if len(token) > 4 and token.endswith("s"):
                        singular = token[:-1]
                        variants.append(singular)
                        variants.extend(_CATEGORY_SYNONYMS.get(singular, ()))
                    variants.extend(_CATEGORY_SYNONYMS.get(token, ()))
                    variant_conditions = []
                    for variant in variants:
                        pattern = f"%{variant}%"
                        variant_conditions.append(
                            "(lower(p.name) LIKE ? OR lower(coalesce(p.description, '')) LIKE ? "
                            "OR lower(coalesce(c.name, '')) LIKE ? OR lower(coalesce(b.name, '')) LIKE ?)"
                        )
                        parameters.extend([pattern] * 4)
                    parts.append("(" + " OR ".join(variant_conditions) + ")")
                # Every meaningful term must match somewhere in the product row;
                # this avoids returning unrelated items that share only the brand.
                conditions.extend(parts)
            if max_price is not None:
                conditions.append("p.price <= ?")
                parameters.append(max_price)
            where = "WHERE " + " AND ".join(conditions) if conditions else ""

            normalized_question = _normalize(question)
            order = "p.price ASC" if any(
                word in normalized_question for word in ("cheapest", "cheap", "moins cher")
            ) else "p.name COLLATE NOCASE"
            rows = connection.execute(
                f"SELECT p.name, p.price, p.stock, c.name AS category, b.name AS brand "
                f"FROM products p "
                f"LEFT JOIN categories c ON c.id = p.category_id "
                f"LEFT JOIN brands b ON b.id = p.brand_id "
                f"{where} ORDER BY {order} LIMIT 5",
                parameters,
            ).fetchall()
    except sqlite3.Error:
        return "La base locale n'est pas encore prête pour la recherche de produits."

    if not rows:
        return "Je n'ai trouvé aucun produit correspondant dans la base locale."
    return "Produits trouvés dans la base locale :\n" + "\n".join(
        f"- {row['name']} — {row['price']:.2f}"
        + (f" | catégorie : {row['category']}" if row["category"] else "")
        + (f" | marque : {row['brand']}" if row["brand"] else "")
        + f" | stock : {row['stock']}"
        for row in rows
    )


def answer_local(question: str) -> str:
    """Answer from the local FAQ or SQLite database without contacting a model."""
    faq_answer = _faq_section(question)
    availability_question = _has_availability_intent(question)
    if availability_question and _mentions_catalog_identifier(question):
        return _local_product_search(question)
    if faq_answer:
        return f"Réponse issue de la FAQ locale :\n{faq_answer}"
    if availability_question or any(word in _normalize(question) for word in _PRODUCT_WORDS):
        return _local_product_search(question)
    return (
        "Mode local activé : je peux répondre à partir de la FAQ sur la livraison, "
        "les retours, la garantie, le paiement et le contact."
    )
