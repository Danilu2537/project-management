from fastapi import FastAPI
from settings import settings
from routing.employee import router as employee_router
from routing.projects import router as projects_router
from fastapi.middleware.cors import CORSMiddleware


def create_app():
    application = FastAPI()
    application.include_router(employee_router, prefix=settings.API_V1_STR)
    application.include_router(projects_router, prefix=settings.API_V1_STR)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return application


app = create_app()
