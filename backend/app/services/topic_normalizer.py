import re

# Manual synonym groups for common academic aliases.
# Heuristic: exam PDFs often split one concept into many noisy fragments.
CANONICAL_SYNONYMS: dict[str, list[str]] = {
    "Row Echelon Forms": [
        "row echelon",
        "row echelon form",
        "reduced row echelon",
        "reduced row",
        "rref",
    ],
    "Linear Systems": [
        "system linear",
        "linear system",
        "system linear equations",
        "linear equations",
        "systems of equations",
        "system of linear equations",
    ],
    "Vector Space": [
        "vector spaces",
        "vector space",
    ],
    "Inner Product": [
        "inner products",
        "inner product",
    ],
    "Eigenvalues": [
        "eigenvalue",
        "eigenvalues",
        "eigen value",
        "eigen values",
        "eigen vectors",
        "eigenvectors",
        "eigen vector",
    ],
    "Matrix Operations": [
        "matrix operation",
        "matrix operations",
        "matrix multiplication",
    ],
    "Gaussian Elimination": [
        "gaussian elimination",
        "gauss elimination",
    ],
    "LU Decomposition": [
        "lu decomposition",
        "lu factorization",
    ],
    "Determinants": [
        "determinant",
        "determinants",
    ],
    "Orthogonality": [
        "orthogonal",
        "orthogonality",
        "orthonormal",
    ],
    "Basis and Dimension": [
        "basis dimension",
        "basis and dimension",
        "dimension basis",
    ],
    "Linear Transformations": [
        "linear transformation",
        "linear transformations",
    ],
    "Differential Equations": [
        "differential equation",
        "differential equations",
    ],
    "Fourier Series": [
        "fourier series",
        "fourier transform",
    ],
    "Laplace Transform": [
        "laplace transform",
        "laplace transforms",
    ],
    "Gram Schmidt Process": [
        "gram schmidt",
        "gram schmidt process",
        "gram-schmidt",
    ],
    "Orthogonal Projection": [
        "orthogonal projection",
        "projection orthogonal",
    ],
    "Characteristic Polynomial": [
        "characteristic polynomial",
        "characteristic polynomials",
    ],
    "Matrix Rank": [
        "matrix rank",
        "rank matrix",
    ],
    "Linear Independence": [
        "linear independence",
        "linearly independent",
    ],
    "Orthogonal Basis": [
        "orthogonal basis",
        "orthonormal basis",
    ],
    "Inner Product Space": [
        "inner product space",
    ],
    "Cramer's Rule": [
        "cramer rule",
        "cramers rule",
    ],
}


def _normalize_key(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# Build fast lookup: normalized variant -> canonical display name.
_VARIANT_TO_CANONICAL: dict[str, str] = {}
for canonical_name, variants in CANONICAL_SYNONYMS.items():
    _VARIANT_TO_CANONICAL[_normalize_key(canonical_name)] = canonical_name
    for variant in variants:
        _VARIANT_TO_CANONICAL[_normalize_key(variant)] = canonical_name


def _singularize_last_word(text: str) -> str:
    words = text.split()
    if not words:
        return text
    last = words[-1]
    if last.endswith("s") and len(last) > 3:
        words[-1] = last[:-1]
    return " ".join(words)


def canonicalize_topic(topic: str) -> str:
    """
    Map noisy topic text to one canonical concept name.
    Uses exact match, substring match, then simple singularization.
    """
    key = _normalize_key(topic)
    if not key:
        return topic.strip()

    if key in _VARIANT_TO_CANONICAL:
        return _VARIANT_TO_CANONICAL[key]

    singular_key = _singularize_last_word(key)
    if singular_key in _VARIANT_TO_CANONICAL:
        return _VARIANT_TO_CANONICAL[singular_key]

    # Substring match: choose the longest matching variant for stability.
    best_match = ""
    best_canonical = ""
    for variant, canonical in _VARIANT_TO_CANONICAL.items():
        if variant in key or key in variant:
            if len(variant) > len(best_match):
                best_match = variant
                best_canonical = canonical

    if best_canonical:
        return best_canonical

    # Default: title-case cleaned phrase for readable AI context.
    return " ".join(word.capitalize() for word in key.split())


def merge_topic_frequency(topic_frequency: dict[str, int]) -> dict[str, int]:
    merged: dict[str, int] = {}
    for topic, count in topic_frequency.items():
        canonical = canonicalize_topic(topic)
        merged[canonical] = merged.get(canonical, 0) + count
    return merged


def merge_files_appeared_in(files_appeared_in: dict[str, list[str]]) -> dict[str, list[str]]:
    merged: dict[str, set[str]] = {}
    for topic, files in files_appeared_in.items():
        canonical = canonicalize_topic(topic)
        merged.setdefault(canonical, set()).update(files)
    return {topic: sorted(files) for topic, files in merged.items()}
