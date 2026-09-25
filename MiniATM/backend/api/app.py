from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import account_routes, auth_routes, transaction_routes


def create_app() -> FastAPI:
    app = FastAPI(
        title="MiniATM API",
        description="Modern ATM simulation API",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_routes.router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(account_routes.router, prefix="/api/account", tags=["Account"])
    app.include_router(
        transaction_routes.router,
        prefix="/api/transactions",
        tags=["Transactions"],
    )

    return app


app = create_app()


@app.get("/")
def root():
    return {"message": "MiniATM API", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}
