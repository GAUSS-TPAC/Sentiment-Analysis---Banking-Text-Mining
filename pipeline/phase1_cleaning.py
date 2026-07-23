"""
Phase 1 - Consolidation & nettoyage des reclamations Intercom.

Etapes :
  1. Fusion titre + description -> champ `texte`
  2. Correction des artefacts d'encodage (apostrophes corrompues, caracteres de controle)
  3. Extraction des PII (telephone, montant, reference, date) vers des colonnes dediees,
     et masquage dans `texte` (remplacement par des tokens <TEL>, <MONTANT>, ...)
  4. Detection de la langue (fr/en) par ticket
  5. Lemmatisation avec le pipeline spaCy correspondant a la langue detectee

Sortie : reclamations_phase1.csv, avec les colonnes originales utiles
+ texte, texte_masque, texte_lemmatise, langue, pii_telephones, pii_montants,
  pii_references, pii_dates.

Installation prealable :
    pip install -r requirements_phase1.txt
    python -m spacy download fr_core_news_sm
    python -m spacy download en_core_web_sm
"""

import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
INPUT_CSV = ROOT / "data" / "raw" / "SRC_Intercom_Reclamation_202607201846.csv"
OUTPUT_CSV = ROOT / "data" / "processed" / "reclamations_phase1.csv"

COLUMNS_TO_KEEP = [
    "ticket_id",
    "ticket_attributes__default_title_",
    "ticket_attributes__default_description_",
    "ticket_type_name",
    "channel",
    "created_at",
    "ticket_state_category",
    # champs structures deja fiables (87-93% remplis) : source principale pour les
    # agregations montant/telephone. Les valeurs extraites par regex du texte libre
    # ne servent qu'a nettoyer le NLP et a completer les cas manquants ci-dessous.
    "ticket_attributes_Montant en XAF",
    "ticket_attributes_Numero_tel_client",
]

# --------------------------------------------------------------------------
# 1. Encodage
# --------------------------------------------------------------------------

def fix_encoding(text: str) -> str:
    """Corrige les artefacts recurrents observes dans l'export Intercom."""
    if not isinstance(text, str):
        return ""
    # 0x1A (SUB) remplace systematiquement l'apostrophe francaise dans cet export
    text = text.replace("\x1a", "'")
    # autres caracteres de controle non imprimables
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", text)
    return text.strip()


# --------------------------------------------------------------------------
# 2. Extraction des PII (regex)
# --------------------------------------------------------------------------

# numeros mobiles camerounais : 9 chiffres commencant par 6
RE_PHONE = re.compile(r"\b6\d{8}\b")
# dates jj.mm.aaaa / jj/mm/aaaa / jj-mm-aaaa
RE_DATE = re.compile(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b")
# references de transaction type "W2026062612983391" (lettre(s) + >=8 chiffres)
RE_REFERENCE = re.compile(r"\b[A-Z]{1,3}\d{8,}\b")
# montants : suite de 4 chiffres ou plus, avec separateurs de milliers optionnels
RE_MONTANT = re.compile(r"\b\d{1,3}(?:[ ,]\d{3})+\b|\b\d{4,}\b")


def extract_and_mask(text: str):
    """
    Extrait telephones / dates / references / montants du texte, puis masque
    ces occurrences par des tokens neutres pour ne pas polluer le NLP.
    Retourne (texte_masque, telephones, dates, references, montants).
    """
    phones = RE_PHONE.findall(text)
    masked = RE_PHONE.sub(" <TEL> ", text)

    dates = RE_DATE.findall(masked)
    masked = RE_DATE.sub(" <DATE> ", masked)

    references = RE_REFERENCE.findall(masked)
    masked = RE_REFERENCE.sub(" <REF> ", masked)

    # les montants sont extraits en dernier pour ne pas capturer telephones/references/dates
    montants = RE_MONTANT.findall(masked)
    masked = RE_MONTANT.sub(" <MONTANT> ", masked)

    masked = re.sub(r"\s+", " ", masked).strip()
    return masked, phones, dates, references, montants


# --------------------------------------------------------------------------
# 3. Detection de langue
# --------------------------------------------------------------------------

def detect_language(text: str) -> str:
    if not text or len(text.strip()) < 3:
        return "unknown"
    try:
        from langdetect import detect, LangDetectException
        try:
            lang = detect(text)
        except LangDetectException:
            return "unknown"
        return lang if lang in ("fr", "en") else "other"
    except ImportError:
        return "unknown"


# --------------------------------------------------------------------------
# 4. Lemmatisation (spaCy, pipeline choisi selon la langue)
# --------------------------------------------------------------------------

def load_spacy_pipelines():
    """Charge fr_core_news_sm et en_core_web_sm si disponibles."""
    try:
        import spacy
    except ImportError:
        print("[!] spaCy non installe : la lemmatisation sera ignoree.", file=sys.stderr)
        return None, None

    nlp_fr = nlp_en = None
    try:
        nlp_fr = spacy.load("fr_core_news_sm", disable=["parser", "ner"])
    except OSError:
        print("[!] Modele fr_core_news_sm introuvable "
              "(python -m spacy download fr_core_news_sm).", file=sys.stderr)
    try:
        nlp_en = spacy.load("en_core_web_sm", disable=["parser", "ner"])
    except OSError:
        print("[!] Modele en_core_web_sm introuvable "
              "(python -m spacy download en_core_web_sm).", file=sys.stderr)
    return nlp_fr, nlp_en


# marques/termes metier que le lemmatiseur statistique deforme sinon en "verbes"
# inconnus (ex: SARA -> sarer, orange -> oranger). A completer si d'autres
# deformations apparaissent (verifier avec un echantillon apres chaque run).
PROTECTED_TERMS = {
    "sara", "orange", "momo", "om", "ecobank", "efirst", "mtn",
}


def _lemmatize_doc(doc) -> str:
    tokens = []
    for tok in doc:
        if not tok.is_alpha or tok.is_stop:
            continue
        low = tok.text.lower()
        tokens.append(low if low in PROTECTED_TERMS else tok.lemma_.lower())
    return " ".join(tokens)


def lemmatize_by_language(df: pd.DataFrame, text_col: str, lang_col: str) -> pd.Series:
    nlp_fr, nlp_en = load_spacy_pipelines()
    result = pd.Series([""] * len(df), index=df.index, dtype=object)

    if nlp_fr is not None:
        mask_fr = df[lang_col] == "fr"
        docs = nlp_fr.pipe(df.loc[mask_fr, text_col].tolist(), batch_size=64)
        result.loc[mask_fr] = [_lemmatize_doc(doc) for doc in docs]

    if nlp_en is not None:
        mask_en = df[lang_col] == "en"
        docs = nlp_en.pipe(df.loc[mask_en, text_col].tolist(), batch_size=64)
        result.loc[mask_en] = [_lemmatize_doc(doc) for doc in docs]

    # langue non detectee/autre : on garde le texte masque sans lemmatisation
    remaining = ~df[lang_col].isin(["fr", "en"])
    result.loc[remaining] = df.loc[remaining, text_col]

    return result


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main():
    print(f"Lecture de {INPUT_CSV} ...")
    df = pd.read_csv(INPUT_CSV, low_memory=False)
    df = df[COLUMNS_TO_KEEP].copy()

    # ne garder que les tickets ayant au moins un titre ou une description
    has_text = (
        df["ticket_attributes__default_title_"].notna()
        | df["ticket_attributes__default_description_"].notna()
    )
    df = df[has_text].reset_index(drop=True)
    print(f"{len(df)} tickets avec du texte libre (sur le total du fichier).")

    # 1. fusion titre + description
    title = df["ticket_attributes__default_title_"].fillna("").map(fix_encoding)
    desc = df["ticket_attributes__default_description_"].fillna("").map(fix_encoding)
    df["texte"] = (title + ". " + desc).str.strip(". ").str.replace(r"^\.\s*", "", regex=True)

    # 2. extraction PII + masquage
    extracted = df["texte"].map(extract_and_mask)
    df["texte_masque"] = extracted.map(lambda t: t[0])
    df["pii_telephones"] = extracted.map(lambda t: ";".join(t[1]) if t[1] else "")
    df["pii_dates"] = extracted.map(lambda t: ";".join(t[2]) if t[2] else "")
    df["pii_references"] = extracted.map(lambda t: ";".join(t[3]) if t[3] else "")
    df["pii_montants"] = extracted.map(lambda t: ";".join(t[4]) if t[4] else "")

    # 3. detection de langue (sur le texte masque, plus propre pour le detecteur)
    print("Detection de la langue ...")
    df["langue"] = df["texte_masque"].map(detect_language)
    print(df["langue"].value_counts())

    # 4. lemmatisation selon la langue
    print("Lemmatisation (spaCy) ...")
    df["texte_lemmatise"] = lemmatize_by_language(df, "texte_masque", "langue")

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Ecrit : {OUTPUT_CSV} ({len(df)} lignes, {len(df.columns)} colonnes)")


if __name__ == "__main__":
    main()
