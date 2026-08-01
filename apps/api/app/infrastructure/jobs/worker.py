"""arq worker entrypoint (ADR-024/ADR-026): `arq app.infrastructure.jobs.worker.WorkerSettings`."""
from arq.connections import RedisSettings

from app.core.config import get_settings
from app.infrastructure.jobs.tasks import generate_embeddings


class WorkerSettings:
    functions = [generate_embeddings]
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
