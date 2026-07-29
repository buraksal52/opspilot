from sqlalchemy import text


async def test_database_connection_works(db_session):
    result = await db_session.execute(text("SELECT 1"))

    assert result.scalar_one() == 1


async def test_app_and_analytics_schemas_exist(db_session):
    result = await db_session.execute(
        text("SELECT schema_name FROM information_schema.schemata WHERE schema_name IN ('app', 'analytics')")
    )

    assert {row[0] for row in result.all()} == {"app", "analytics"}
