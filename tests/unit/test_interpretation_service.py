from app.application.analytics.interpretation_service import ResultInterpretationService
from app.application.analytics.results import QueryResult
from app.application.analytics.schemas import AnalysisPlan, AnalyticalIntent
from app.infrastructure.llm.fake_provider import FakeLLMProvider


async def test_interpret_returns_the_llm_text_and_includes_result_values_in_the_prompt():
    llm = FakeLLMProvider()
    llm.queue_text("Refund rate rose from 4.1% to 5.2%.")
    plan = AnalysisPlan(
        intent=AnalyticalIntent(question_type="comparison", metrics=["refund_rate"], dimensions=[], datasets=["orders"]),
        steps=["Compute refund rate before July 11.", "Compute refund rate after July 11."],
    )
    result = QueryResult(columns=["period", "refund_rate"], rows=[["before", 0.041], ["after", 0.052]], row_count=2)

    text = await ResultInterpretationService(llm).interpret(question="Why did refunds increase?", plan=plan, result=result)

    assert text == "Refund rate rose from 4.1% to 5.2%."
    assert len(llm.text_calls) == 1
    assert "0.041" in llm.text_calls[0]
    assert "0.052" in llm.text_calls[0]
