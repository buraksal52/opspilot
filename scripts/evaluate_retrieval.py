"""Manual/live retrieval evaluation — the RAG_SYSTEM.md §37 baseline gate.

Computes Recall@K, Precision@K, and MRR for the vector-only retrieval
baseline (BACKLOG.md 4.4) against the canonical `retrieval`-tagged questions
(DATASET.md §33, `data/northstar/eval/evaluation_questions.json`).

This is deliberately NOT part of `make test-api`: it makes real, paid Gemini
API calls and ingests real documents (TESTING.md §30/§31 — "Full
Evaluation... runs manually... live model calls"). Per RAG_SYSTEM.md §37,
lexical retrieval, fusion, and reranking are only added later if they clear a
measured improvement over the numbers this script reports — it exists to
produce that measurement, not to assert a pass/fail threshold itself.

Usage (requires `make up`'s dev Postgres reachable, and a real GEMINI_API_KEY
in `.env` — see README/.env.example):

    make evaluate-retrieval
"""
import asyncio
import json
import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))

from app.application.ingestion.document_ingestion_service import DocumentIngestionService  # noqa: E402
from app.application.retrieval.chunking_service import ChunkingService  # noqa: E402
from app.application.retrieval.embedding_service import EmbeddingGenerationService  # noqa: E402
from app.application.retrieval.hybrid_search_service import HybridSearchService  # noqa: E402
from app.application.retrieval.lexical_search_service import LexicalSearchService  # noqa: E402
from app.application.retrieval.reranking_service import RerankingService  # noqa: E402
from app.application.retrieval.vector_search_service import VectorSearchService  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.domain.data_source import SourceType  # noqa: E402
from app.infrastructure.auth.password_hasher import PasswordHasher  # noqa: E402
from app.infrastructure.database.repositories.data_source_repository import DataSourceRepository  # noqa: E402
from app.infrastructure.database.repositories.document_chunk_repository import DocumentChunkRepository  # noqa: E402
from app.infrastructure.database.repositories.document_repository import DocumentRepository  # noqa: E402
from app.infrastructure.database.repositories.user_repository import UserRepository  # noqa: E402
from app.infrastructure.database.repositories.workspace_repository import WorkspaceRepository  # noqa: E402
from app.infrastructure.database.session import async_session_factory  # noqa: E402
from app.infrastructure.embeddings.gemini_provider import GeminiEmbeddingProvider  # noqa: E402
from app.infrastructure.rerankers.gemini_reranker import GeminiReranker  # noqa: E402

DOCS_DIR = REPO_ROOT / "data" / "northstar" / "documents"
EVAL_QUESTIONS_PATH = REPO_ROOT / "data" / "northstar" / "eval" / "evaluation_questions.json"

# title -> filename, matching DATASET.md §19/§27.
DOCUMENT_FILES = {
    "Refund Policy": "Refund Policy.pdf",
    "Shipping Policy": "Shipping Policy.pdf",
    "Customer Support Handbook": "Customer Support Handbook.pdf",
    "Shipping Provider Migration Report": "Shipping Provider Migration Report.pdf",
    "July Operations Incident Report": "July Operations Incident Report.pdf",
}

TOP_K = 5


async def _ingest_all_documents(session, workspace_id: uuid.UUID) -> list[uuid.UUID]:
    settings = get_settings()
    ingestion_service = DocumentIngestionService(
        DocumentRepository(session),
        DocumentChunkRepository(session),
        ChunkingService(target_tokens=settings.chunk_target_tokens, overlap_tokens=settings.chunk_overlap_tokens),
    )
    data_source_repo = DataSourceRepository(session)

    document_ids = []
    for title, filename in DOCUMENT_FILES.items():
        path = DOCS_DIR / filename
        if not path.exists():
            raise SystemExit(f"Missing {path} — run `make generate-northstar` first.")
        content = path.read_bytes()
        data_source = await data_source_repo.create(
            workspace_id=workspace_id,
            name=title,
            source_type=SourceType.PDF,
            original_filename=filename,
            mime_type="application/pdf",
            file_size_bytes=len(content),
            storage_key=f"eval/{workspace_id}/{uuid.uuid4()}.pdf",
        )
        document = await ingestion_service.ingest(
            workspace_id=workspace_id,
            data_source_id=data_source.id,
            source_type=SourceType.PDF,
            title=title,
            content=content,
        )
        document_ids.append(document.id)
    await session.commit()
    return document_ids


async def _embed_all_documents(session, document_ids: list[uuid.UUID]) -> None:
    settings = get_settings()
    provider = GeminiEmbeddingProvider(
        api_key=settings.gemini_api_key, model=settings.embedding_model, output_dimension=settings.embedding_dimension
    )
    embedding_service = EmbeddingGenerationService(DocumentChunkRepository(session), provider, settings.embedding_model)
    for document_id in document_ids:
        await embedding_service.generate_for_document(document_id)
    await session.commit()


async def _evaluate(search_service, questions: list[dict], workspace_id: uuid.UUID, *, label: str) -> dict:
    recalls, precisions, reciprocal_ranks = [], [], []
    print(f"\n=== {label} ===")
    print(f"{'ID':<12} {'Question':<55} {'Result':<6} {'Rank':<6} Fact found")
    for question in questions:
        results = await search_service.search(workspace_id=workspace_id, query=question["question"], limit=TOP_K)
        expected_doc = question["expected_document"]
        matches = [r for r in results if r.document_title == expected_doc]
        hit = bool(matches)
        rank = next((i + 1 for i, r in enumerate(results) if r.document_title == expected_doc), None)

        recalls.append(1.0 if hit else 0.0)
        precisions.append(len(matches) / len(results) if results else 0.0)
        reciprocal_ranks.append(1.0 / rank if rank else 0.0)

        expected_fact = question.get("expected_fact", "").lower()
        fact_found = any(expected_fact in r.content.lower() for r in matches) if expected_fact else None
        print(
            f"{question['id']:<12} {question['question'][:53]:<55} "
            f"{'HIT' if hit else 'MISS':<6} {rank or '-':<6} {fact_found}"
        )

    n = len(questions)
    metrics = {
        "recall": sum(recalls) / n,
        "precision": sum(precisions) / n,
        "mrr": sum(reciprocal_ranks) / n,
    }
    print(f"\nRecall@{TOP_K}:    {metrics['recall']:.2f}")
    print(f"Precision@{TOP_K}: {metrics['precision']:.2f}")
    print(f"MRR:          {metrics['mrr']:.2f}")
    return metrics


async def _cleanup(session, workspace_id: uuid.UUID, user_id: uuid.UUID) -> None:
    from sqlalchemy import text

    await session.execute(text("DELETE FROM app.document_chunks WHERE workspace_id = :wid"), {"wid": workspace_id})
    await session.execute(text("DELETE FROM app.documents WHERE workspace_id = :wid"), {"wid": workspace_id})
    await session.execute(text("DELETE FROM app.data_sources WHERE workspace_id = :wid"), {"wid": workspace_id})
    await session.execute(text("DELETE FROM app.workspaces WHERE id = :wid"), {"wid": workspace_id})
    await session.execute(text("DELETE FROM app.users WHERE id = :uid"), {"uid": user_id})
    await session.commit()


async def main() -> None:
    settings = get_settings()
    if settings.gemini_api_key.startswith("changeme"):
        raise SystemExit(
            "GEMINI_API_KEY is not set to a real key (.env still has the placeholder). "
            "This evaluation makes real Gemini API calls and needs one — see .env.example."
        )

    questions = [q for q in json.loads(EVAL_QUESTIONS_PATH.read_text()) if "retrieval" in q["tags"]]
    if not questions:
        raise SystemExit(f"No 'retrieval'-tagged questions found in {EVAL_QUESTIONS_PATH}.")

    async with async_session_factory() as session:
        user = await UserRepository(session).create(
            email=f"eval-{uuid.uuid4().hex[:8]}@opspilot.local",
            hashed_password=PasswordHasher().hash("evaluation-only-not-a-real-account"),
        )
        workspace = await WorkspaceRepository(session).create(
            name="Retrieval Evaluation", slug=f"retrieval-eval-{uuid.uuid4().hex[:8]}", owner_id=user.id
        )
        await session.commit()

        try:
            print(f"Ingesting {len(DOCUMENT_FILES)} Northstar documents into workspace {workspace.id}...")
            document_ids = await _ingest_all_documents(session, workspace.id)

            print("Generating embeddings (real Gemini API calls)...")
            await _embed_all_documents(session, document_ids)

            provider = GeminiEmbeddingProvider(
                api_key=settings.gemini_api_key,
                model=settings.embedding_model,
                output_dimension=settings.embedding_dimension,
            )
            chunk_repo = DocumentChunkRepository(session)
            document_repo = DocumentRepository(session)
            vector_service = VectorSearchService(chunk_repo, document_repo, provider)
            lexical_service = LexicalSearchService(chunk_repo, document_repo)
            hybrid_service = HybridSearchService(vector_service, lexical_service, settings.retrieval_candidate_limit)
            reranker = GeminiReranker(api_key=settings.gemini_api_key, model=settings.reranker_model)
            reranked_service = RerankingService(vector_service, reranker, settings.retrieval_candidate_limit)

            vector_metrics = await _evaluate(vector_service, questions, workspace.id, label="Vector-only baseline")
            hybrid_metrics = await _evaluate(hybrid_service, questions, workspace.id, label="Hybrid (RRF fusion)")
            reranked_metrics = await _evaluate(
                reranked_service, questions, workspace.id, label="Vector + Reranking"
            )

            print("\n=== Comparison ===")
            print(f"{'Metric':<12} {'Vector-only':<14} {'Hybrid':<14} {'+Reranking':<14}")
            for key in ("recall", "precision", "mrr"):
                print(
                    f"{key:<12} {vector_metrics[key]:<14.2f} {hybrid_metrics[key]:<14.2f} {reranked_metrics[key]:<14.2f}"
                )

            print(
                "\nRecord these numbers in docs/DECISIONS.md (ADR-029/ADR-030) before deciding whether "
                "hybrid fusion/reranking (BACKLOG.md 4.6-4.7) clear RAG_SYSTEM.md §37's gate — only keep "
                "a stage that shows a measured improvement over the previous best baseline."
            )
        finally:
            await _cleanup(session, workspace.id, user.id)


if __name__ == "__main__":
    asyncio.run(main())
