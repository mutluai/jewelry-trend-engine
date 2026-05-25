from .product import ProductCreate, ProductRead, ProductList
from .trend import TrendSignalRead, TrendSignalList
from .scoring import OpportunityScoreRead, OpportunityList
from .report import ReportRead, ReportList
from .connector import ConnectorStatusRead, ConnectorRunResponse
from .settings import AppSettingRead, AppSettingUpdate, ScoringWeights

__all__ = [
    "ProductCreate", "ProductRead", "ProductList",
    "TrendSignalRead", "TrendSignalList",
    "OpportunityScoreRead", "OpportunityList",
    "ReportRead", "ReportList",
    "ConnectorStatusRead", "ConnectorRunResponse",
    "AppSettingRead", "AppSettingUpdate", "ScoringWeights",
]
