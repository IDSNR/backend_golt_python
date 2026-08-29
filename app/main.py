from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from data_management.database import init_db
from app.api.health import router as health_router
from app.api.routes.profiles import router as profiles_router
from app.api.routes.wallet import router as wallet_router
from app.api.routes.companies import router as companies_router
from app.api.routes.auth import router as auth_router
from app.api.routes.content import router as content_router
from app.api.routes.engagement import router as engagement_router
from app.api.routes.groups import router as groups_router
from app.api.routes.media import router as media_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.purchases import router as purchases_router
from app.api.routes.referrals import router as referrals_router
from app.api.routes.reports import router as reports_router
from app.api.routes.sends import router as sends_router
from app.api.routes.social import router as social_router
from app.api.routes.stories import router as stories_router
from app.api.routes.subscriptions import router as subscriptions_router
from app.api.routes.feed import router as feed_router
from app.api.routes.follows import router as follows_router
from app.api.routes.search import router as search_router
from app.api.routes.dms import router as dms_router
from app.api.routes.roulette import router as roulette_router
from app.api.routes.realtime import router as realtime_router
from app.api.routes.admin import router as admin_router
from app.core.rate_limit import RateLimitMiddleware

@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.db_auto_create:
        init_db()
    yield


app = FastAPI(title="PartnerHub Python Backend", lifespan=lifespan)
app.add_middleware(RateLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(profiles_router)
app.include_router(wallet_router)
app.include_router(auth_router)
app.include_router(content_router)
app.include_router(engagement_router)
app.include_router(groups_router)
app.include_router(social_router)
app.include_router(companies_router)
app.include_router(notifications_router)
app.include_router(purchases_router)
app.include_router(referrals_router)
app.include_router(reports_router)
app.include_router(sends_router)
app.include_router(stories_router)
app.include_router(subscriptions_router)
app.include_router(search_router)
app.include_router(dms_router)
app.include_router(roulette_router)
app.include_router(feed_router)
app.include_router(follows_router)
app.include_router(media_router)
app.include_router(realtime_router)
app.include_router(admin_router)

# A fresh checkout does not contain the ignored upload folder. Create it before
# StaticFiles validates the path when local development storage is selected.
if settings.media_storage_backend == "local":
    Path(settings.media_folder).mkdir(parents=True, exist_ok=True)
    app.mount(settings.media_url_path, StaticFiles(directory=settings.media_folder), name="media")
