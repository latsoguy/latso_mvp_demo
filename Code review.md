## Overview
- **App Purpose**: Refer instructions provided in project 
- **Tech Stack**: Python, react and supabase with OpenAI API for GPT 
- **Architecture Oveview**: My main file atm other than main.py is the IntegratedProjectWorflow which interlinks to other files.  

---
## File: main.py
```python
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
'''
---

---
## File: App.js
```js
import React, { useState } from 'react';

function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [scenarioDelay, setScenarioDelay] = useState(2);

  // REALISTIC project data with REAL reasoning
  const projectMetrics = {
    totalBudget: 75000000,
    spentToDate: 27800000,
    budgetRemaining: 47200000,
    totalDays: 245,
    daysElapsed: 118,
    daysRemaining: 127,
    overallCompletion: 58
  };

  const workPackages = [
    { 
      id: 1,
      name: 'Electrical Systems', 
      completion: 45, 
      risk: 'HIGH',
      budgetAllocated: 18000000,
      spent: 8100000,
      vendor: 'ABC Electrical',
      criticalPath: true,
      issueCount: 3,
      lastUpdate: '2 hours ago'
    },
    { 
      id: 2,
      name: 'Foundation & Structural', 
      completion: 78, 
      risk: 'LOW',
      budgetAllocated: 12000000,
      spent: 9360000,
      vendor: 'Steelworks Pro',
      criticalPath: false,
      issueCount: 0,
      lastUpdate: '1 day ago'
    },
    { 
      id: 3,
      name: 'HVAC Installation', 
      completion: 52, 
      risk: 'MEDIUM',
      budgetAllocated: 15000000,
      spent: 7800000,
      vendor: 'HVAC Solutions',
      criticalPath: true,
      issueCount: 1,
      lastUpdate: '4 hours ago'
    },
    { 
      id: 4,
      name: 'Fire Safety Systems', 
      completion: 89, 
      risk: 'LOW',
      budgetAllocated: 8000000,
      spent: 7120000,
      vendor: 'SafeGuard Fire',
      criticalPath: false,
      issueCount: 0,
      lastUpdate: '1 day ago'
    },
    { 
      id: 5,
      name: 'IT Infrastructure', 
      completion: 34, 
      risk: 'MEDIUM',
      budgetAllocated: 12000000,
      spent: 4080000,
      vendor: 'TechNet Systems',
      criticalPath: true,
      issueCount: 2,
      lastUpdate: '6 hours ago'
    },
    { 
      id: 6,
      name: 'Exterior Cladding', 
      completion: 67, 
      risk: 'LOW',
      budgetAllocated: 10000000,
      spent: 6700000,
      vendor: 'Steelworks Pro',
      criticalPath: false,
      issueCount: 0,
      lastUpdate: '3 hours ago'
    }
  ];

  // REALISTIC electrical risk with ACTUAL cost breakdown
  const electricalRisk = {
    title: 'Electrical Systems - Critical Path Delay Risk',
    workPackageId: 1,
    riskLevel: 'HIGH',
    probability: 78,
    costImpactBreakdown: {
      laborOverrun: 1200000, // 3 weeks additional labor at $400K/week
      materialPremium: 450000, // Rush delivery premium on electrical components
      liquidatedDamages: 650000, // Contractual penalties to client for late delivery
      cascadingDelays: 0, // HVAC and IT teams waiting (included in labor)
      total: 2300000
    },
    scheduleImpact: {
      directDelay: 18, // Electrical work itself
      criticalPathExtension: 18, // Extends overall project completion
      description: 'Electrical is on critical path - any delay extends project completion'
    },
    reasoning: 'ABC Electrical missed 3 consecutive milestones (switchgear delivery, main panel installation, circuit testing). Current burn rate indicates 78% probability of 3-week delay based on similar past projects.',
    mitigations: [
      { 
        title: 'Dual-source critical components', 
        cost: 180000, 
        timeToImplement: '5 days', 
        riskReduction: 45,
        description: 'Secure backup suppliers for remaining switchgear and panels to reduce single-vendor dependency'
      },
      { 
        title: 'Accelerate penalty enforcement', 
        cost: 0, 
        timeToImplement: '2 days', 
        riskReduction: 25,
        description: 'Trigger contractual penalties immediately to incentivize performance improvement'
      },
      { 
        title: 'Deploy backup electrical contractor', 
        cost: 340000, 
        timeToImplement: '14 days', 
        riskReduction: 70,
        description: 'Bring in secondary qualified contractor to work parallel on non-interfering portions'
      }
    ]
  };

  const getRiskColor = (level) => {
    switch (level) {
      case 'HIGH': return { bg: '#fef2f2', border: '#fca5a5', text: '#7f1d1d', dot: '#dc2626' };
      case 'MEDIUM': return { bg: '#fffbeb', border: '#fcd34d', text: '#92400e', dot: '#f59e0b' };
      case 'LOW': return { bg: '#f0fdf4', border: '#86efac', text: '#166534', dot: '#10b981' };
      default: return { bg: '#f9fafb', border: '#d1d5db', text: '#374151', dot: '#6b7280' };
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', { 
      style: 'currency', 
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const Dashboard = () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* PROJECT OVERVIEW - Top priority for PM */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
        {/* Project Heatmap - MAIN FOCUS */}
        <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '24px', border: '1px solid #e5e7eb' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#111827', margin: 0 }}>Work Package Status</h2>
            <div style={{ fontSize: '14px', color: '#6b7280' }}>Last updated: 2 hours ago</div>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
            {workPackages.map((pkg) => {
              const colors = getRiskColor(pkg.risk);
              return (
                <div 
                  key={pkg.id}
                  style={{ 
                    padding: '20px', 
                    borderRadius: '8px', 
                    border: `2px solid ${colors.border}`,
                    backgroundColor: colors.bg,
                    cursor: pkg.risk === 'HIGH' ? 'pointer' : 'default',
                    transition: 'all 0.2s'
                  }}
                  onClick={() => pkg.risk === 'HIGH' ? setCurrentView('risk-detail') : null}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                    <div style={{ flex: 1 }}>
                      <h3 style={{ fontSize: '16px', fontWeight: '600', color: colors.text, margin: '0 0 4px 0' }}>
                        {pkg.name}
                      </h3>
                      <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>
                        {pkg.vendor} • {formatCurrency(pkg.spent)} of {formatCurrency(pkg.budgetAllocated)}
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{ 
                        width: '8px', 
                        height: '8px', 
                        borderRadius: '50%', 
                        backgroundColor: colors.dot 
                      }}></div>
                      <span style={{ fontSize: '12px', fontWeight: '600', color: colors.text }}>
                        {pkg.risk}
                      </span>
                    </div>
                  </div>
                  
                  <div style={{ marginBottom: '12px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                      <span style={{ fontSize: '14px', color: '#374151' }}>Progress</span>
                      <span style={{ fontSize: '14px', fontWeight: '600', color: '#374151' }}>{pkg.completion}%</span>
                    </div>
                    <div style={{ width: '100%', height: '8px', backgroundColor: '#f3f4f6', borderRadius: '4px', overflow: 'hidden' }}>
                      <div style={{ 
                        width: `${pkg.completion}%`, 
                        height: '100%', 
                        backgroundColor: colors.dot,
                        transition: 'width 0.3s'
                      }}></div>
                    </div>
                  </div>
                  
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px', color: '#6b7280' }}>
                    <span>{pkg.criticalPath ? '🔥 Critical Path' : 'Non-critical'}</span>
                    <span>{pkg.issueCount} open issues</span>
                  </div>
                  
                  {pkg.risk === 'HIGH' && (
                    <div style={{ marginTop: '12px', fontSize: '12px', color: colors.text, fontWeight: '500' }}>
                      → Click for detailed analysis
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Executive Summary */}
        <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '24px', border: '1px solid #e5e7eb' }}>
          <h2 style={{ fontSize: '18px', fontWeight: '600', color: '#111827', marginBottom: '20px' }}>Project Summary</h2>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '4px' }}>Overall Progress</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#111827' }}>{projectMetrics.overallCompletion}%</div>
              <div style={{ fontSize: '12px', color: '#6b7280' }}>Day {projectMetrics.daysElapsed} of {projectMetrics.totalDays}</div>
            </div>
            
            <div>
              <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '4px' }}>Budget Status</div>
              <div style={{ fontSize: '18px', fontWeight: '600', color: '#111827' }}>
                {formatCurrency(projectMetrics.budgetRemaining)}
              </div>
              <div style={{ fontSize: '12px', color: '#6b7280' }}>
                {formatCurrency(projectMetrics.spentToDate)} spent • {Math.round((projectMetrics.spentToDate/projectMetrics.totalBudget)*100)}% utilized
              </div>
            </div>
            
            <div>
              <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '4px' }}>Schedule Status</div>
              <div style={{ fontSize: '18px', fontWeight: '600', color: '#111827' }}>{projectMetrics.daysRemaining} days</div>
              <div style={{ fontSize: '12px', color: '#6b7280' }}>Until contractual completion</div>
            </div>
          </div>
          
          <div style={{ marginTop: '20px', padding: '16px', backgroundColor: '#fef2f2', borderRadius: '8px', border: '1px solid #fecaca' }}>
            <div style={{ fontSize: '14px', fontWeight: '600', color: '#7f1d1d', marginBottom: '8px' }}>⚠️ Immediate Attention Required</div>
            <div style={{ fontSize: '13px', color: '#991b1b' }}>
              Electrical package on critical path showing delivery risks. Potential {formatCurrency(electricalRisk.costImpactBreakdown.total)} impact if not addressed.
            </div>
          </div>
        </div>
      </div>

      {/* CRITICAL RISKS - Second priority */}
      <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '24px', border: '1px solid #e5e7eb' }}>
        <h2 style={{ fontSize: '18px', fontWeight: '600', color: '#111827', marginBottom: '20px' }}>Critical Risk Analysis</h2>
        
        <div style={{ padding: '20px', backgroundColor: '#fef2f2', borderRadius: '8px', border: '1px solid #fecaca' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#7f1d1d', margin: '0 0 4px 0' }}>
                {electricalRisk.title}
              </h3>
              <div style={{ fontSize: '14px', color: '#991b1b' }}>
                {electricalRisk.probability}% probability • Critical path impact
              </div>
            </div>
            <button
              onClick={() => setCurrentView('risk-detail')}
              style={{
                padding: '8px 16px',
                backgroundColor: '#dc2626',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '500',
                cursor: 'pointer'
              }}
            >
              Analyze →
            </button>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '16px' }}>
            <div>
              <div style={{ fontSize: '12px', color: '#7f1d1d', marginBottom: '4px' }}>COST IMPACT</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#7f1d1d' }}>
                {formatCurrency(electricalRisk.costImpactBreakdown.total)}
              </div>
              <div style={{ fontSize: '11px', color: '#991b1b' }}>
                Labor overrun + Material premium + Liquidated damages
              </div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: '#7f1d1d', marginBottom: '4px' }}>SCHEDULE IMPACT</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#7f1d1d' }}>
                +{electricalRisk.scheduleImpact.directDelay} days
              </div>
              <div style={{ fontSize: '11px', color: '#991b1b' }}>
                Extends overall project completion
              </div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: '#7f1d1d', marginBottom: '4px' }}>MITIGATION COST</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#7f1d1d' }}>
                {formatCurrency(180000)}
              </div>
              <div style={{ fontSize: '11px', color: '#991b1b' }}>
                Dual-sourcing recommendation
              </div>
            </div>
          </div>
          
          <div style={{ fontSize: '13px', color: '#991b1b' }}>
            <strong>Root Cause:</strong> {electricalRisk.reasoning}
          </div>
        </div>
      </div>

      {/* ACTION ITEMS */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
        <button 
          onClick={() => setCurrentView('scenario')}
          style={{ 
            backgroundColor: 'white', 
            borderRadius: '8px', 
            padding: '20px', 
            border: '1px solid #e5e7eb',
            cursor: 'pointer',
            textAlign: 'left',
            transition: 'all 0.2s'
          }}
        >
          <div style={{ fontSize: '20px', marginBottom: '8px' }}>📊</div>
          <h3 style={{ fontSize: '14px', fontWeight: '600', color: '#111827', margin: '0 0 4px 0' }}>Scenario Modeling</h3>
          <p style={{ fontSize: '12px', color: '#6b7280', margin: 0 }}>Impact analysis & planning</p>
        </button>
        
        <button 
          onClick={() => setCurrentView('vendors')}
          style={{ 
            backgroundColor: 'white', 
            borderRadius: '8px', 
            padding: '20px', 
            border: '1px solid #e5e7eb',
            cursor: 'pointer',
            textAlign: 'left'
          }}
        >
          <div style={{ fontSize: '20px', marginBottom: '8px' }}>🏢</div>
          <h3 style={{ fontSize: '14px', fontWeight: '600', color: '#111827', margin: '0 0 4px 0' }}>Vendor Performance</h3>
          <p style={{ fontSize: '12px', color: '#6b7280', margin: 0 }}>Contractor scorecards</p>
        </button>
        
        <button 
          onClick={() => setCurrentView('brief')}
          style={{ 
            backgroundColor: 'white', 
            borderRadius: '8px', 
            padding: '20px', 
            border: '1px solid #e5e7eb',
            cursor: 'pointer',
            textAlign: 'left'
          }}
        >
          <div style={{ fontSize: '20px', marginBottom: '8px' }}>📋</div>
          <h3 style={{ fontSize: '14px', fontWeight: '600', color: '#111827', margin: '0 0 4px 0' }}>Executive Report</h3>
          <p style={{ fontSize: '12px', color: '#6b7280', margin: 0 }}>Stakeholder summary</p>
        </button>

        <div style={{ 
          backgroundColor: '#f0fdf4', 
          borderRadius: '8px', 
          padding: '20px', 
          border: '1px solid #86efac'
        }}>
          <div style={{ fontSize: '20px', marginBottom: '8px' }}>⏱️</div>
          <h3 style={{ fontSize: '14px', fontWeight: '600', color: '#166534', margin: '0 0 4px 0' }}>Time Efficiency</h3>
          <p style={{ fontSize: '12px', color: '#166534', margin: 0 }}>
            Auto-analysis replaces 2.5 hours of manual status compilation and risk assessment
          </p>
        </div>
      </div>
    </div>
  );

  const RiskDetail = () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <button 
          onClick={() => setCurrentView('dashboard')}
          style={{ 
            padding: '8px 12px',
            backgroundColor: '#f3f4f6',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          ← Back to Dashboard
        </button>
        <h1 style={{ fontSize: '24px', fontWeight: '600', color: '#111827', margin: 0 }}>
          Risk Analysis: {electricalRisk.title}
        </h1>
      </div>

      {/* COST IMPACT BREAKDOWN - Show the REAL math */}
      <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '24px', border: '1px solid #e5e7eb' }}>
        <h2 style={{ fontSize: '18px', fontWeight: '600', color: '#111827', marginBottom: '20px' }}>
          Cost Impact Analysis: {formatCurrency(electricalRisk.costImpactBreakdown.total)}
        </h2>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '20px' }}>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#374151', marginBottom: '12px' }}>Cost Breakdown</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px', backgroundColor: '#f9fafb', borderRadius: '4px' }}>
                <span style={{ fontSize: '14px', color: '#374151' }}>Extended Labor Costs</span>
                <span style={{ fontSize: '14px', fontWeight: '600' }}>{formatCurrency(electricalRisk.costImpactBreakdown.laborOverrun)}</span>
              </div>
              <div style={{ fontSize: '12px', color: '#6b7280', marginLeft: '8px', marginBottom: '8px' }}>
                3 weeks additional work @ $400K/week (crew of 12 electricians + supervision)
              </div>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px', backgroundColor: '#f9fafb', borderRadius: '4px' }}>
                <span style={{ fontSize: '14px', color: '#374151' }}>Material Rush Premium</span>
                <span style={{ fontSize: '14px', fontWeight: '600' }}>{formatCurrency(electricalRisk.costImpactBreakdown.materialPremium)}</span>
              </div>
              <div style={{ fontSize: '12px', color: '#6b7280', marginLeft: '8px', marginBottom: '8px' }}>
                Expedited delivery of switchgear and electrical panels (25% premium on $1.8M materials)
              </div>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px', backgroundColor: '#f9fafb', borderRadius: '4px' }}>
                <span style={{ fontSize: '14px', color: '#374151' }}>Liquidated Damages</span>
                <span style={{ fontSize: '14px', fontWeight: '600' }}>{formatCurrency(electricalRisk.costImpactBreakdown.liquidatedDamages)}</span>
              </div>
              <div style={{ fontSize: '12px', color: '#6b7280', marginLeft: '8px' }}>
                Contractual penalty to client for late delivery ($36K/day × 18 days)
              </div>
            </div>
          </div>
          
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#374151', marginBottom: '12px' }}>Schedule Impact</h3>
            <div style={{ padding: '16px', backgroundColor: '#fef2f2', borderRadius: '8px', border: '1px solid #fecaca' }}>
              <div style={{ fontSize: '14px', color: '#7f1d1d', marginBottom: '8px' }}>
                <strong>Critical Path Extension: +{electricalRisk.scheduleImpact.directDelay} days</strong>
              </div>
              <div style={{ fontSize: '13px', color: '#991b1b', lineHeight: '1.4' }}>
                Electrical work gates HVAC rough-in and IT infrastructure installation. 
                Any electrical delay directly extends project completion date.
              </div>
            </div>
            
            <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#374151', marginTop: '20px', marginBottom: '12px' }}>Risk Probability</h3>
            <div style={{ padding: '16px', backgroundColor: '#f9fafb', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
              <div style={{ fontSize: '14px', color: '#374151', marginBottom: '8px' }}>
                <strong>{electricalRisk.probability}% Probability Assessment</strong>
              </div>
              <div style={{ fontSize: '13px', color: '#6b7280', lineHeight: '1.4' }}>
                Based on: 3 consecutive missed milestones, current resource deployment rate, 
                and historical performance data from 8 similar electrical packages.
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* MITIGATION OPTIONS */}
      <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '24px', border: '1px solid #e5e7eb' }}>
        <h2 style={{ fontSize: '18px', fontWeight: '600', color: '#111827', marginBottom: '20px' }}>
          Mitigation Strategies
        </h2>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {electricalRisk.mitigations.map((mitigation, idx) => (
            <div key={idx} style={{ 
              border: '1px solid #e5e7eb', 
              borderRadius: '8px', 
              padding: '20px',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                <div style={{ flex: 1 }}>
                  <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#111827', margin: '0 0 8px 0' }}>
                    {mitigation.title}
                  </h3>
                  <p style={{ fontSize: '14px', color: '#6b7280', margin: '0 0 12px 0', lineHeight: '1.4' }}>
                    {mitigation.description}
                  </p>
                </div>
                <div style={{ textAlign: 'right', marginLeft: '20px' }}>
                  <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#059669' }}>
                    -{mitigation.riskReduction}% risk
                  </div>
                </div>
              </div>
              
              <div style={{ display: 'flex', gap: '24px', fontSize: '14px' }}>
                <div>
                  <span style={{ color: '#6b7280' }}>Investment: </span>
                  <span style={{ fontWeight: '600', color: '#111827' }}>
                    {mitigation.cost === 0 ? 'No cost' : formatCurrency(mitigation.cost)}
                  </span>
                </div>
                <div>
                  <span style={{ color: '#6b7280' }}>Implementation: </span>
                  <span style={{ fontWeight: '600', color: '#111827' }}>{mitigation.timeToImplement}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const ScenarioPlanning = () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <button 
          onClick={() => setCurrentView('dashboard')}
          style={{ 
            padding: '8px 12px',
            backgroundColor: '#f3f4f6',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          ← Back to Dashboard
        </button>
        <h1 style={{ fontSize: '24px', fontWeight: '600', color: '#111827', margin: 0 }}>
          Scenario Impact Modeling
        </h1>
      </div>

      <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '24px', border: '1px solid #e5e7eb' }}>
        <div style={{ marginBottom: '24px' }}>
          <h2 style={{ fontSize: '18px', fontWeight: '600', color: '#111827', marginBottom: '8px' }}>
            Electrical Package Delay Analysis
          </h2>
          <p style={{ fontSize: '14px', color: '#6b7280', margin: 0 }}>
            Model different delay scenarios to understand cost and schedule impacts
          </p>
        </div>
        
        <div style={{ marginBottom: '32px' }}>
          <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#374151', marginBottom: '8px' }}>
            Delay Duration: {scenarioDelay} weeks
          </label>
          <input 
            type="range" 
            min="1" 
            max="8" 
            value={scenarioDelay}
            onChange={(e) => setScenarioDelay(parseInt(e.target.value))}
            style={{ 
              width: '100%',
              height: '8px',
              borderRadius: '4px',
              background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${(scenarioDelay/8)*100}%, #e5e7eb ${(scenarioDelay/8)*100}%, #e5e7eb 100%)`,
              outline: 'none',
              cursor: 'pointer'
            }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
            <span>1 week</span>
            <span>4 weeks</span>
            <span>8 weeks</span>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '32px' }}>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#111827', marginBottom: '16px' }}>
              Current Baseline (2 weeks)
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', backgroundColor: '#f9fafb', borderRadius: '6px' }}>
                <span style={{ color: '#6b7280' }}>Cost Impact:</span>
                <span style={{ fontWeight: '600', color: '#dc2626' }}>{formatCurrency(electricalRisk.costImpactBreakdown.total)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', backgroundColor: '#f9fafb', borderRadius: '6px' }}>
                <span style={{ color: '#6b7280' }}>Schedule Impact:</span>
                <span style={{ fontWeight: '600', color: '#dc2626' }}>+{electricalRisk.scheduleImpact.directDelay} days</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', backgroundColor: '#f9fafb', borderRadius: '6px' }}>
                <span style={{ color: '#6b7280' }}>New Completion:</span>
                <span style={{ fontWeight: '600' }}>Mar 15, 2025</span>
              </div>
            </div>
          </div>
          
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#111827', marginBottom: '16px' }}>
              Scenario Analysis ({scenarioDelay} weeks)
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', backgroundColor: '#f9fafb', borderRadius: '6px' }}>
                <span style={{ color: '#6b7280' }}>Cost Impact:</span>
                <span style={{ fontWeight: '600', color: '#dc2626' }}>
                  {formatCurrency(electricalRisk.costImpactBreakdown.total * (scenarioDelay / 2))}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', backgroundColor: '#f9fafb', borderRadius: '6px' }}>
                <span style={{ color: '#6b7280' }}>Schedule Impact:</span>
                <span style={{ fontWeight: '600', color: '#dc2626' }}>+{Math.round(electricalRisk.scheduleImpact.directDelay * (scenarioDelay / 2))} days</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', backgroundColor: '#f9fafb', borderRadius: '6px' }}>
                <span style={{ color: '#6b7280' }}>New Completion:</span>
                <span style={{ fontWeight: '600' }}>Mar {15 + Math.round((scenarioDelay / 2) * 9)}, 2025</span>
              </div>
            </div>
          </div>
        </div>

        <div style={{ marginTop: '24px', padding: '16px', backgroundColor: scenarioDelay > 4 ? '#fef2f2' : '#eff6ff', borderRadius: '8px', border: `1px solid ${scenarioDelay > 4 ? '#fecaca' : '#bfdbfe'}` }}>
          <div style={{ fontSize: '14px', fontWeight: '600', color: scenarioDelay > 4 ? '#7f1d1d' : '#1e40af', marginBottom: '4px' }}>
            Impact Assessment:
          </div>
          <div style={{ fontSize: '13px', color: scenarioDelay > 4 ? '#991b1b' : '#1e3a8a' }}>
            {scenarioDelay > 4 
              ? 'CRITICAL - Would trigger executive escalation, client penalty discussions, and potential contract renegotiation'
              : scenarioDelay > 2 
                ? 'SIGNIFICANT - Requires immediate mitigation action and stakeholder notification'
                : 'MANAGEABLE - Within acceptable risk tolerance with current mitigation options'
            }
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f8fafc' }}>
      {/* Header */}
      <header style={{ backgroundColor: 'white', borderBottom: '1px solid #e5e7eb', padding: '16px 0' }}>
        <div style={{ maxWidth: '100%', margin: '0 auto', padding: '0 32px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h1 style={{ fontSize: '28px', fontWeight: 'bold', color: '#111827', margin: 0 }}>LATSO</h1>
              <p style={{ color: '#6b7280', margin: 0, fontSize: '14px' }}>Port Expansion Project - Phase 2 Control Center</p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '14px', color: '#111827', fontWeight: '500' }}>Andrew Chen</div>
                <div style={{ fontSize: '12px', color: '#6b7280' }}>Senior Project Manager</div>
              </div>
              <div style={{ width: '40px', height: '40px', backgroundColor: '#2563eb', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ color: 'white', fontWeight: '600', fontSize: '16px' }}>AC</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ maxWidth: '100%', margin: '0 auto', padding: '32px' }}>
        {currentView === 'dashboard' && <Dashboard />}
        {currentView === 'risk-detail' && <RiskDetail />}
        {currentView === 'scenario' && <ScenarioPlanning />}
      </main>
    </div>
  );
}

export default App;
```
---
