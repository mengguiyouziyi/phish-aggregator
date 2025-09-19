"""
视觉钓鱼检测API路由
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict
import asyncio
from ..services.visual_detector import visual_detector, initialize_targets

router = APIRouter()

class TargetSiteRequest(BaseModel):
    """目标网站请求模型"""
    url: str
    name: str

class DetectionRequest(BaseModel):
    """检测请求模型"""
    url: str
    compare_targets: Optional[List[str]] = None
    threshold: Optional[float] = 0.85

class DetectionResponse(BaseModel):
    """检测响应模型"""
    is_phishing: bool
    confidence: float
    message: str
    processing_time: Optional[float] = None
    best_match: Optional[str] = None
    similarity_threshold: float
    comparison_results: Optional[Dict] = None
    screenshot_path: Optional[str] = None

class TargetListResponse(BaseModel):
    """目标列表响应模型"""
    targets: List[Dict]

@router.post("/targets", response_model=Dict)
async def add_target_site(request: TargetSiteRequest):
    """添加目标网站"""
    try:
        success = await visual_detector.add_known_target(request.url, request.name)
        if success:
            return {"success": True, "message": f"成功添加目标网站: {request.name}"}
        else:
            raise HTTPException(status_code=400, detail="添加目标网站失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/targets", response_model=TargetListResponse)
async def get_target_sites():
    """获取所有目标网站"""
    try:
        targets = visual_detector.get_known_targets()
        return TargetListResponse(targets=targets)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/targets/{target_name}")
async def remove_target_site(target_name: str):
    """移除目标网站"""
    try:
        success = visual_detector.remove_target(target_name)
        if success:
            return {"success": True, "message": f"成功移除目标网站: {target_name}"}
        else:
            raise HTTPException(status_code=404, detail="目标网站不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/detect", response_model=DetectionResponse)
async def detect_phishing(request: DetectionRequest):
    """检测网站是否为钓鱼网站"""
    try:
        result = await visual_detector.detect_phishing(
            url=request.url,
            compare_targets=request.compare_targets,
        )

        return DetectionResponse(
            is_phishing=result["is_phishing"],
            confidence=result["confidence"],
            message=result["message"],
            processing_time=result.get("processing_time"),
            best_match=result.get("best_match"),
            similarity_threshold=result.get("similarity_threshold", 0.85),
            comparison_results=result.get("comparison_results"),
            screenshot_path=result.get("screenshot_path")
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/initialize")
async def initialize_detection_system(background_tasks: BackgroundTasks):
    """初始化检测系统（添加常见目标网站）"""
    try:
        background_tasks.add_task(initialize_targets)
        return {
            "success": True,
            "message": "系统初始化已启动，正在添加常见目标网站..."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_detection_status():
    """获取检测系统状态"""
    try:
        target_count = len(visual_detector.known_targets)
        return {
            "status": "active",
            "known_targets_count": target_count,
            "device": str(visual_detector.device),
            "model_loaded": visual_detector.model is not None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))