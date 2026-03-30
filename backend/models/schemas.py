"""Pydantic schemas for API request/response models."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any


class Coordinate(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lng: float = Field(..., ge=-180, le=180, description="Longitude")


class ScoreRequest(BaseModel):
    lat: float = Field(..., description="Latitude of the point to score")
    lng: float = Field(..., description="Longitude of the point to score")
    weights: Optional[Dict[str, float]] = Field(None, description="Custom weights for each layer")
    preset: Optional[str] = Field(None, description="Use case preset name")
    radius_km: float = Field(5.0, description="Analysis radius in km")


class PolygonScoreRequest(BaseModel):
    polygon: List[List[float]] = Field(..., description="Polygon coordinates [[lng,lat],...]")
    weights: Optional[Dict[str, float]] = None
    preset: Optional[str] = None
    h3_resolution: int = Field(7, ge=4, le=9)


class SubScore(BaseModel):
    layer: str
    score: float
    weight: float
    weighted_score: float
    details: Dict[str, Any] = {}


class ScoreResponse(BaseModel):
    lat: float
    lng: float
    composite_score: float
    grade: str
    sub_scores: List[SubScore]
    threshold_violations: List[str] = []
    nearby_summary: Dict[str, Any] = {}


class CompareRequest(BaseModel):
    sites: List[Coordinate]
    weights: Optional[Dict[str, float]] = None
    preset: Optional[str] = None


class ClusterRequest(BaseModel):
    h3_resolution: int = Field(7, ge=4, le=9)
    min_samples: int = Field(3, ge=2)
    eps_km: float = Field(10.0, description="DBSCAN epsilon in km")
    weights: Optional[Dict[str, float]] = None
    preset: Optional[str] = None


class IsochroneRequest(BaseModel):
    lat: float
    lng: float
    mode: str = Field("driving", description="driving or walking")
    intervals: List[int] = Field([10, 20, 30], description="Minutes")


class ExportRequest(BaseModel):
    sites: List[Coordinate]
    format: str = Field("pdf", description="pdf or json")
    weights: Optional[Dict[str, float]] = None
    preset: Optional[str] = None
    title: str = Field("Site Readiness Report", description="Report title")


class HeatmapRequest(BaseModel):
    h3_resolution: int = Field(7, ge=4, le=9)
    bounds: Optional[Dict[str, float]] = None
    weights: Optional[Dict[str, float]] = None
    preset: Optional[str] = None
