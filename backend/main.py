from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from pydantic import BaseModel
from typing import List, Optional
import os
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase setup with error handling
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY")

if not url:
    print("❌ ERROR: SUPABASE_URL not found in environment variables")
    print("Make sure your .env file contains:")
    print("SUPABASE_URL=your_supabase_project_url")
    exit(1)

if not key:
    print("❌ ERROR: SUPABASE_ANON_KEY not found in environment variables") 
    print("Make sure your .env file contains:")
    print("SUPABASE_ANON_KEY=your_supabase_anon_key")
    exit(1)

try:
    supabase: Client = create_client(url, key)
    print("✅ Successfully connected to Supabase")
except Exception as e:
    print(f"❌ Failed to connect to Supabase: {e}")
    exit(1)

# Models
class RiskAnalysis(BaseModel):
    work_package_id: str
    delay_weeks: int

class ScenarioResult(BaseModel):
    budget_impact: float
    schedule_impact: int
    completion_date: str
    risk_level: str

class VendorScore(BaseModel):
    vendor_id: str
    on_time: int
    quality: int
    cost: int
    communication: int

@app.get("/")
async def root():
    return {"message": "LATSO Demo API is running!", "status": "healthy"}

@app.get("/api/project/{project_id}/dashboard")
async def get_dashboard(project_id: str):
    """Get dashboard data for Andrew's Monday morning briefing"""
    
    try:
        # Get project data
        project = supabase.table('projects').select('*').eq('id', project_id).execute()
        
        # Get work packages with risk levels
        work_packages = supabase.table('work_packages').select('*, vendors(name)').eq('project_id', project_id).execute()
        
        # Get top risks
        risks = supabase.table('risks').select('*, work_packages(name)').order('impact_cost', desc=True).limit(3).execute()
        
        # Calculate AI briefing
        critical_items = []
        for risk in risks.data:
            if risk['risk_level'] == 'HIGH':
                critical_items.append({
                    'title': risk['title'],
                    'impact': f"${risk['impact_cost']/1000000:.1f}M cost, {risk['impact_days']} days delay",
                    'reasoning': risk['reasoning']
                })
        
        return {
            'project': project.data[0] if project.data else None,
            'work_packages': work_packages.data,
            'critical_items': critical_items,
            'time_saved_today': '4.5 hrs'  # Mock calculation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/scenario/analyze")
async def analyze_scenario(analysis: RiskAnalysis):
    """Run what-if scenario analysis"""
    
    try:
        # Get base risk data
        risk = supabase.table('risks').select('*').eq('work_package_id', analysis.work_package_id).execute()
        
        if not risk.data:
            raise HTTPException(status_code=404, detail="Risk not found")
        
        base_risk = risk.data[0]
        
        # Calculate scaled impact based on delay multiplier
        multiplier = analysis.delay_weeks / 2  # Base scenario is 2 weeks
        
        new_budget_impact = base_risk['impact_cost'] * multiplier
        new_schedule_impact = base_risk['impact_days'] * multiplier
        
        # Calculate new completion date
        base_date = datetime.now() + timedelta(days=127)  # 127 days remaining
        new_date = base_date + timedelta(days=new_schedule_impact)
        
        # Determine risk level
        if analysis.delay_weeks > 3:
            risk_level = "CRITICAL"
        elif analysis.delay_weeks > 2:
            risk_level = "HIGH"
        else:
            risk_level = "MEDIUM"
        
        return ScenarioResult(
            budget_impact=new_budget_impact,
            schedule_impact=int(new_schedule_impact),
            completion_date=new_date.strftime("%b %d, %Y"),
            risk_level=risk_level
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

@app.get("/api/vendors")
async def get_vendor_performance():
    """Get vendor performance dashboard"""
    
    try:
        vendors = supabase.table('vendors').select('*, vendor_alerts(*)').execute()
        
        vendor_data = []
        for vendor in vendors.data:
            # Calculate composite score
            scores = {
                'on_time': vendor['on_time_delivery'],
                'quality': vendor['quality_score'],
                'cost': vendor['cost_performance'],
                'communication': vendor['communication_score']
            }
            
            # Weighted average (matching your brief specs)
            composite_score = (
                scores['on_time'] * 0.35 +
                scores['quality'] * 0.25 +
                scores['cost'] * 0.25 +
                scores['communication'] * 0.15
            )
            
            vendor_data.append({
                'id': vendor['id'],
                'name': vendor['name'],
                'score': int(composite_score),
                'trend': vendor['trend'],
                'alerts': [alert['message'] for alert in vendor['vendor_alerts'] if alert['is_active']],
                'detailed_scores': scores
            })
        
        return vendor_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vendor data error: {str(e)}")

@app.post("/api/vendor/{vendor_id}/update-score")
async def update_vendor_score(vendor_id: str, scores: VendorScore):
    """Update vendor performance scores"""
    
    try:
        # Calculate composite score
        composite = (
            scores.on_time * 0.35 +
            scores.quality * 0.25 +
            scores.cost * 0.25 +
            scores.communication * 0.15
        )
        
        # Update vendor
        supabase.table('vendors').update({
            'on_time_delivery': scores.on_time,
            'quality_score': scores.quality,
            'cost_performance': scores.cost,
            'communication_score': scores.communication,
            'performance_score': int(composite)
        }).eq('id', vendor_id).execute()
        
        return {'success': True, 'new_score': int(composite)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update error: {str(e)}")

@app.get("/api/risks/{risk_id}/mitigations")
async def get_risk_mitigations(risk_id: str):
    """Get mitigation options for a specific risk"""
    
    try:
        mitigations = supabase.table('mitigations').select('*').eq('risk_id', risk_id).execute()
        return mitigations.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mitigation data error: {str(e)}")

@app.post("/api/executive-brief/generate")
async def generate_executive_brief(project_id: str):
    """Generate executive brief in 10 seconds (mock AI generation)"""
    
    # This would normally call your AI service
    # For demo, returning structured data
    
    brief = {
        'generated_at': datetime.now().isoformat(),
        'generation_time': '10 seconds',
        'time_saved': '3 hours',
        'project_health': 'At Risk',
        'top_risks': [
            'Electrical Package Performance: ABC Electrical showing 67% compliance',
            'IT Infrastructure Delays: 34% completion vs 45% planned',
            'HVAC Material Supply: 3-day delivery delays impacting schedule'
        ],
        'recommendations': [
            'Implement dual-source procurement for electrical switchgear (+$180K)',
            'Activate penalty clauses for ABC Electrical (triggers in 14 days)',
            'Accelerate IT infrastructure contractor onboarding'
        ],
        'budget_status': {
            'remaining': 47200000,
            'at_risk': 2300000
        },
        'schedule_status': {
            'days_remaining': 127,
            'at_risk_days': 18
        }
    }
    
    return brief

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting LATSO Demo API...")
    uvicorn.run(app, host="0.0.0.0", port=8000)