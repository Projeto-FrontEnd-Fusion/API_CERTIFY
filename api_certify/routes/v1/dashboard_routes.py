from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api_certify.core.database.mongodb import db_mongo
from api_certify.dependencies import require_role
from api_certify.service.dashboard_service import DashboardService


class MonthlyEmissions(BaseModel):
    month: str
    emissions: int


class RecentActivity(BaseModel):
    id: str
    name: str = 'Certificado'
    student: str = 'Participante'
    issued_at: datetime


class DashboardData(BaseModel):
    issued: int
    pending_delivery: int
    sent: int
    participants: int
    emissions: list[MonthlyEmissions]
    recent_activities: list[RecentActivity]


class DashboardResponse(BaseModel):
    success: bool = True
    data: DashboardData


dashboard_routes = APIRouter(prefix='/dashboard', tags=['Dashboard'])


async def get_dashboard_service():
    return DashboardService(await db_mongo.get_database())


@dashboard_routes.get('', response_model=DashboardResponse)
async def get_dashboard(
    user: dict = Depends(require_role('empresa')),
    service: DashboardService = Depends(get_dashboard_service),
):
    return DashboardResponse(data=await service.summary(user['sub']))
