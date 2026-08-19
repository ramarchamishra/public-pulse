import asyncio

from services.analysis.ingestion_service import IngestionService


async def main():
    topic = input("Enter topic: ")
    limit = int(input("Number of tweets: "))

    service = IngestionService()

    result = await service.ingest_topic(
        topic=topic,
        limit=limit,
        mode="Mixed"
    )

    print("\nCompleted!")
    print(f"Search ID     : {result['search_id']}")
    print(f"Tweets Stored : {result['tweets_saved']}")


if __name__ == "__main__":
    asyncio.run(main())