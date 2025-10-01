import uvicorn

from src.config import settings


def run():
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        use_colors=True,
    )


if __name__ == "__main__":
    run()
