from api.app.summary import make_summary


def test_base_summary_uses_only_base_statistics_and_explains_fdr_scope() -> None:
    summary = make_summary("Amazon example box", 0.02, 0.01, 0.03, 0.01, 0.02)

    assert "OLS t=0.010" in summary["en"]
    assert "Mann-Kendall=0.020" in summary["en"]
    assert "Hamed-Rao" not in summary["en"]
    assert "No spatial FDR correction applies" in summary["en"]
    assert "La correction FDR spatiale" in summary["fr"]


def test_summary_adds_detected_pettitt_candidate_in_both_languages() -> None:
    summary = make_summary(
        "Test region",
        0.02,
        0.01,
        0.03,
        0.01,
        0.02,
        break_result={"date": "2005-06", "p": 0.004},
    )

    assert "2005-06" in summary["en"] and "p=0.004" in summary["en"]
    assert "p=0.004" in summary["fr"]
