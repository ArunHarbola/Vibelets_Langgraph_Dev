from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
import shutil
import tempfile

from facebook.client import fb_get
from facebook.campaigns import create_campaign
from facebook.adsets import create_adset
from facebook.ads import create_video_ad
from facebook.media import upload_media_service

router = APIRouter(prefix="/facebook", tags=["Facebook Ads"])

# --- Pydantic Models ---

class CampaignRequest(BaseModel):
    account_id: str
    name: str
    objective: str
    access_token: Optional[str] = None
    special_ad_categories: Optional[List[str]] = None

class AdSetRequest(BaseModel):
    account_id: str
    campaign_id: str
    name: str
    daily_budget: float
    start_time: str
    end_time: str
    access_token: Optional[str] = None
    targeting: Optional[Dict] = None

class VideoAdRequest(BaseModel):
    account_id: str
    adset_id: str
    page_id: str
    ad_name: str
    video_id: str
    thumbnail_hash: str
    message: str
    link: str
    access_token: Optional[str] = None

# --- Endpoints ---

@router.post("/campaigns")
async def create_campaign_endpoint(request: CampaignRequest):
    token = request.access_token or os.getenv("META_ACCESS_TOKEN")
    if not token:
        raise HTTPException(status_code=400, detail="Access token required")
        
    try:
        result = await create_campaign(
            account_id=request.account_id,
            name=request.name,
            objective=request.objective,
            access_token=token,
            special_ad_categories=request.special_ad_categories
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/adsets")
async def create_adset_endpoint(request: AdSetRequest):
    token = request.access_token or os.getenv("META_ACCESS_TOKEN")
    if not token:
        raise HTTPException(status_code=400, detail="Access token required")
        
    try:
        result = await create_adset(
            account_id=request.account_id,
            campaign_id=request.campaign_id,
            name=request.name,
            daily_budget=request.daily_budget,
            start_time=request.start_time,
            end_time=request.end_time,
            access_token=token,
            targeting=request.targeting
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ads/video")
async def create_video_ad_endpoint(request: VideoAdRequest):
    token = request.access_token or os.getenv("META_ACCESS_TOKEN")
    if not token:
        raise HTTPException(status_code=400, detail="Access token required")
        
    try:
        result = await create_video_ad(
            account_id=request.account_id,
            adset_id=request.adset_id,
            page_id=request.page_id,
            ad_name=request.ad_name,
            video_id=request.video_id,
            thumbnail_hash=request.thumbnail_hash,
            message=request.message,
            link=request.link,
            access_token=token
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/media/upload")
async def upload_media_endpoint(
    account_id: str = Form(...),
    media_type: str = Form(...),
    access_token: Optional[str] = Form(None),
    file: UploadFile = File(...)
):
    token = access_token or os.getenv("META_ACCESS_TOKEN")
    if not token:
        raise HTTPException(status_code=400, detail="Access token required")
    
    # Save uploaded file to temp
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
        
    try:
        result = upload_media_service(
            account_id=account_id,
            media_type=media_type,
            access_token=token,
            temp_path=tmp_path
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)