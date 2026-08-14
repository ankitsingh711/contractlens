from app.evaluation.metrics import compute_case_metrics, faithfulness_score, lexical_overlap


def test_lexical_overlap_identical_text_is_one():
    assert lexical_overlap("seven days notice", "seven days notice") == 1.0


def test_lexical_overlap_disjoint_text_is_zero():
    assert lexical_overlap("seven days notice", "unrelated pricing terms") == 0.0


def test_lexical_overlap_empty_text_is_zero():
    assert lexical_overlap("", "something") == 0.0


def test_faithfulness_score_all_sentences_cited():
    assert faithfulness_score("Termination requires 7 days notice. [1] It also caps liability. [2]") == 1.0


def test_faithfulness_score_no_sentences_cited():
    assert faithfulness_score("Termination requires 7 days notice. It also caps liability.") == 0.0


def test_faithfulness_score_partial_citation():
    assert faithfulness_score("Cited claim. [1] Uncited claim.") == 0.5


def test_case_metrics_correct_grounded_answer_passes():
    metrics = compute_case_metrics(
        should_abstain=False,
        abstained=False,
        retrieved_sections={"8.2", "9"},
        expected_sections={"8.2"},
        citation_sections={"8.2"},
        answer="Either party may terminate with 7 days notice. [1]",
        expected_answer="Termination requires 7 days written notice.",
    )
    assert metrics.passed is True
    assert metrics.hallucinated is False
    assert metrics.citation_accuracy == 1.0
    assert metrics.retrieval_recall == 1.0


def test_case_metrics_wrong_citation_is_hallucination():
    metrics = compute_case_metrics(
        should_abstain=False,
        abstained=False,
        retrieved_sections={"3"},
        expected_sections={"8.2"},
        citation_sections={"3"},
        answer="Payment is due in thirty days. [1]",
        expected_answer="Termination requires 7 days written notice.",
    )
    assert metrics.passed is False
    assert metrics.hallucinated is True
    assert metrics.citation_accuracy == 0.0


def test_case_metrics_correct_abstention_passes():
    metrics = compute_case_metrics(
        should_abstain=True,
        abstained=True,
        retrieved_sections=set(),
        expected_sections=set(),
        citation_sections=set(),
        answer="I couldn't determine this from the provided documents.",
        expected_answer=None,
    )
    assert metrics.passed is True
    assert metrics.hallucinated is False


def test_case_metrics_answering_when_should_abstain_is_hallucination():
    metrics = compute_case_metrics(
        should_abstain=True,
        abstained=False,
        retrieved_sections={"3"},
        expected_sections=set(),
        citation_sections={"3"},
        answer="The penalty is $500. [1]",
        expected_answer=None,
    )
    assert metrics.passed is False
    assert metrics.hallucinated is True


def test_case_metrics_incorrectly_abstaining_fails_but_is_not_hallucination():
    metrics = compute_case_metrics(
        should_abstain=False,
        abstained=True,
        retrieved_sections={"8.2"},
        expected_sections={"8.2"},
        citation_sections=set(),
        answer="I couldn't determine this from the provided documents.",
        expected_answer="Termination requires 7 days written notice.",
    )
    assert metrics.passed is False
    assert metrics.hallucinated is False
