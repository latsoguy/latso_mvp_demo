from supabase import create_client, Client
import os
from datetime import datetime, timedelta
import uuid
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Supabase setup with better error handling
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

print(f"✅ Loading Supabase URL: {url[:30]}...")
print(f"✅ Loading Supabase Key: {key[:20]}...")

try:
    supabase: Client = create_client(url, key)
    print("✅ Successfully connected to Supabase")
except Exception as e:
    print(f"❌ Failed to connect to Supabase: {e}")
    exit(1)

def seed_demo_data():
    """Seed database with Andrew's Port Expansion Project data"""
    
    print("🌱 Starting to seed demo data...")
    
    # Create project
    project_id = str(uuid.uuid4())
    project = {
        'id': project_id,
        'name': 'Port Expansion Project - Phase 2',
        'description': 'Major port infrastructure expansion including electrical, HVAC, and structural work',
        'budget': 75000000.00,
        'start_date': '2024-08-01',
        'end_date': '2025-03-31',
        'status': 'active'
    }
    
    try:
        supabase.table('projects').insert(project).execute()
        print("✅ Created project")
    except Exception as e:
        print(f"❌ Error creating project: {e}")
        return
    
    # Create vendors
    vendors_data = [
        {
            'id': str(uuid.uuid4()),
            'name': 'ABC Electrical',
            'contact_email': 'pm@abcelectrical.com',
            'performance_score': 67,
            'on_time_delivery': 60,
            'quality_score': 80,
            'cost_performance': 65,
            'communication_score': 70,
            'trend': 'down'
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Steelworks Pro',
            'contact_email': 'contact@steelworkspro.com',
            'performance_score': 89,
            'on_time_delivery': 95,
            'quality_score': 88,
            'cost_performance': 85,
            'communication_score': 90,
            'trend': 'up'
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'HVAC Solutions',
            'contact_email': 'pm@hvacsolutions.com',
            'performance_score': 72,
            'on_time_delivery': 70,
            'quality_score': 75,
            'cost_performance': 70,
            'communication_score': 75,
            'trend': 'stable'
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'SafeGuard Fire',
            'contact_email': 'projects@safeguardfire.com',
            'performance_score': 94,
            'on_time_delivery': 98,
            'quality_score': 95,
            'cost_performance': 90,
            'communication_score': 95,
            'trend': 'up'
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'TechNet Systems',
            'contact_email': 'delivery@technetsystems.com',
            'performance_score': 68,
            'on_time_delivery': 65,
            'quality_score': 70,
            'cost_performance': 68,
            'communication_score': 70,
            'trend': 'down'
        }
    ]
    
    try:
        for vendor in vendors_data:
            supabase.table('vendors').insert(vendor).execute()
        print("✅ Created 5 vendors")
    except Exception as e:
        print(f"❌ Error creating vendors: {e}")
        return
    
    # Create work packages
    work_packages_data = [
        {
            'id': str(uuid.uuid4()),
            'project_id': project_id,
            'name': 'Foundation & Structural',
            'budget': 12000000.00,
            'completion_percentage': 78,
            'status': 'in-progress',
            'risk_level': 'LOW',
            'vendor_id': vendors_data[1]['id']  # Steelworks Pro
        },
        {
            'id': str(uuid.uuid4()),
            'project_id': project_id,
            'name': 'Electrical Systems',
            'budget': 18000000.00,
            'completion_percentage': 45,
            'status': 'at-risk',
            'risk_level': 'HIGH',
            'vendor_id': vendors_data[0]['id']  # ABC Electrical
        },
        {
            'id': str(uuid.uuid4()),
            'project_id': project_id,
            'name': 'HVAC Installation',
            'budget': 15000000.00,
            'completion_percentage': 52,
            'status': 'at-risk',
            'risk_level': 'MEDIUM',
            'vendor_id': vendors_data[2]['id']  # HVAC Solutions
        },
        {
            'id': str(uuid.uuid4()),
            'project_id': project_id,
            'name': 'Fire Safety Systems',
            'budget': 8000000.00,
            'completion_percentage': 89,
            'status': 'in-progress',
            'risk_level': 'LOW',
            'vendor_id': vendors_data[3]['id']  # SafeGuard Fire
        },
        {
            'id': str(uuid.uuid4()),
            'project_id': project_id,
            'name': 'IT Infrastructure',
            'budget': 12000000.00,
            'completion_percentage': 34,
            'status': 'at-risk',
            'risk_level': 'MEDIUM',
            'vendor_id': vendors_data[4]['id']  # TechNet Systems
        },
        {
            'id': str(uuid.uuid4()),
            'project_id': project_id,
            'name': 'Exterior Cladding',
            'budget': 10000000.00,
            'completion_percentage': 67,
            'status': 'in-progress',
            'risk_level': 'LOW',
            'vendor_id': vendors_data[1]['id']  # Steelworks Pro
        }
    ]
    
    try:
        for wp in work_packages_data:
            supabase.table('work_packages').insert(wp).execute()
        print("✅ Created 6 work packages")
    except Exception as e:
        print(f"❌ Error creating work packages: {e}")
        return
    
    # Create the critical electrical risk
    electrical_risk = {
        'id': str(uuid.uuid4()),
        'work_package_id': work_packages_data[1]['id'],  # Electrical Systems
        'title': 'Electrical Package - Vendor Performance Decline',
        'description': 'ABC Electrical showing declining performance across multiple metrics',
        'impact_cost': 2300000.00,
        'impact_days': 18,
        'probability': 85,
        'risk_level': 'HIGH',
        'reasoning': 'ABC Electrical missed 3/5 recent milestones. Historical pattern shows 85% probability of 2-week delay. Contract compliance at 67% and declining.',
        'confidence_level': 85
    }
    
    try:
        risk_result = supabase.table('risks').insert(electrical_risk).execute()
        risk_id = risk_result.data[0]['id']
        print("✅ Created critical electrical risk")
    except Exception as e:
        print(f"❌ Error creating risk: {e}")
        return
    
    # Create mitigation options
    mitigations = [
        {
            'risk_id': risk_id,
            'title': 'Dual-source switchgear procurement',
            'description': 'Secure secondary supplier for critical electrical components',
            'cost': 180000.00,
            'time_to_implement': '5 days',
            'risk_reduction_percentage': 45,
            'status': 'proposed'
        },
        {
            'risk_id': risk_id,
            'title': 'Accelerate contractor penalties',
            'description': 'Trigger contractual penalty clauses immediately',
            'cost': 0.00,
            'time_to_implement': '2 days',
            'risk_reduction_percentage': 25,
            'status': 'proposed'
        },
        {
            'risk_id': risk_id,
            'title': 'Bring backup vendor online',
            'description': 'Activate pre-qualified backup electrical contractor',
            'cost': 340000.00,
            'time_to_implement': '14 days',
            'risk_reduction_percentage': 70,
            'status': 'proposed'
        }
    ]
    
    try:
        for mitigation in mitigations:
            supabase.table('mitigations').insert(mitigation).execute()
        print("✅ Created 3 mitigation options")
    except Exception as e:
        print(f"❌ Error creating mitigations: {e}")
        return
    
    # Create vendor alerts
    alerts = [
        {
            'vendor_id': vendors_data[0]['id'],  # ABC Electrical
            'alert_type': 'performance',
            'message': '3 consecutive missed milestones',
            'severity': 'high',
            'is_active': True
        },
        {
            'vendor_id': vendors_data[0]['id'],  # ABC Electrical
            'alert_type': 'contract',
            'message': 'Penalty clause triggers in 14 days',
            'severity': 'high',
            'is_active': True
        },
        {
            'vendor_id': vendors_data[2]['id'],  # HVAC Solutions
            'alert_type': 'delivery',
            'message': 'Material delivery 3 days late',
            'severity': 'medium',
            'is_active': True
        },
        {
            'vendor_id': vendors_data[4]['id'],  # TechNet Systems
            'alert_type': 'communication',
            'message': 'RFI response time exceeded',
            'severity': 'medium',
            'is_active': True
        }
    ]
    
    try:
        for alert in alerts:
            supabase.table('vendor_alerts').insert(alert).execute()
        print("✅ Created vendor alerts")
    except Exception as e:
        print(f"❌ Error creating alerts: {e}")
        return
    
    print("🎉 Demo data seeded successfully!")
    print(f"📋 Project ID: {project_id}")
    print("🚀 You're ready for the demo!")

if __name__ == "__main__":
    seed_demo_data()