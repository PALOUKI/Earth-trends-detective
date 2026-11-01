"""Deterministic bilingual summaries for regional trend results."""

from __future__ import annotations


def make_summary(
    label: str,
    slope: float | None,
    lo: float | None,
    hi: float | None,
    p_ols: float | None,
    p_mk: float | None,
    p_hamed_rao: float | None,
    unit: str = "K/year",
) -> dict[str, str]:
    if slope is None or lo is None or hi is None:
        return {
            "en": (
                f"There are not enough valid monthly observations for {label} "
                "to estimate a trend."
            ),
            "fr": (
                f"Il n’y a pas assez d’observations mensuelles valides pour estimer "
                f"une tendance pour {label}."
            ),
        }
    if p_ols is not None and p_ols < 0.05:
        verdict_en, verdict_fr = "statistically significant", "statistiquement significative"
        caveat_en = caveat_fr = ""
    else:
        verdict_en = "not (yet) statistically significant"
        verdict_fr = "pas (encore) statistiquement significative"
        caveat_en = " A longer period could change this result."
        caveat_fr = " Une période plus longue pourrait changer ce résultat."
    direction_en = "increased" if slope >= 0 else "decreased"
    direction_fr = "augmenté" if slope >= 0 else "diminué"

    def p_text(value: float | None) -> str:
        if value is None:
            return "unavailable"
        if value < 0.001:
            return "<0.001"
        return f"{value:.3f}"

    tests_en = (
        f"Test p-values: OLS t={p_text(p_ols)}, Mann-Kendall={p_text(p_mk)}, "
        f"Hamed-Rao={p_text(p_hamed_rao)}. "
        "No spatial FDR correction applies to one selected region."
    )
    tests_fr = (
        f"Valeurs p : test t MCO={p_text(p_ols)}, Mann-Kendall={p_text(p_mk)}, "
        f"Hamed-Rao={p_text(p_hamed_rao)}. "
        "La correction FDR spatiale ne s’applique pas à une seule région."
    )
    return {
        "en": (
            f"Surface temperature anomaly {direction_en} in {label} by {slope:.4f} {unit} "
            f"(95% confidence interval {lo:.4f} to {hi:.4f}); the linear trend is "
            f"{verdict_en} by the t test. {tests_en}{caveat_en}"
        ),
        "fr": (
            f"L’anomalie de température de surface a {direction_fr} dans {label} de "
            f"{slope:.4f} {unit} (intervalle de confiance à 95 % : {lo:.4f} à {hi:.4f}) ; "
            f"la tendance linéaire est {verdict_fr} selon le test t. {tests_fr}{caveat_fr}"
        ),
    }
