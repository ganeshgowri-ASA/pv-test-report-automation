"""
FastAPI Main Application
PV Test Report Automation System - API Server
"""

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from datetime import datetime

# Create FastAPI app
app = FastAPI(
    title="PV Test Automation API",
    description="RESTful API for PV Test Report Automation System",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "PV Test Automation API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration"""
    return {
        "status": "healthy",
        "service": "api-server",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.getenv("APP_ENV", "development"),
        "checks": {
            "database": "connected",
            "redis": "connected",
            "storage": "connected"
        }
    }


@app.get("/api/v1/protocols")
async def list_protocols():
    """List available IEC protocols"""
    protocols = [
        {
            "id": "iec_61215",
            "name": "IEC 61215",
            "title": "Terrestrial PV Modules - Design Qualification",
            "version": "2021"
        },
        {
            "id": "iec_61730",
            "name": "IEC 61730",
            "title": "PV Module Safety Qualification",
            "version": "2016"
        },
        {
            "id": "iec_61853",
            "name": "IEC 61853",
            "title": "PV Module Performance Testing",
            "version": "2018"
        },
        {
            "id": "iec_62716",
            "name": "IEC 62716",
            "title": "Ammonia Corrosion Testing",
            "version": "2013"
        },
        {
            "id": "iec_61701",
            "name": "IEC 61701",
            "title": "Salt Mist Corrosion Testing",
            "version": "2020"
        },
        {
            "id": "iec_62804",
            "name": "IEC 62804",
            "title": "PID Testing",
            "version": "2015"
        },
        {
            "id": "iec_60904",
            "name": "IEC 60904",
            "title": "PV Device Measurement",
            "version": "2020"
        },
        {
            "id": "iec_62759",
            "name": "IEC 62759",
            "title": "Transportation Testing",
            "version": "2019"
        }
    ]
    return {"protocols": protocols, "count": len(protocols)}


@app.get("/api/v1/tests")
async def list_tests():
    """List test records"""
    # Mock data - replace with actual database queries
    tests = [
        {
            "test_id": "PV-2024-1247",
            "protocol": "IEC 61215",
            "sample": "Solar Module A",
            "status": "Completed",
            "date": "2024-11-20"
        },
        {
            "test_id": "PV-2024-1246",
            "protocol": "IEC 61730",
            "sample": "Solar Module B",
            "status": "In Progress",
            "date": "2024-11-19"
        }
    ]
    return {"tests": tests, "count": len(tests)}


@app.get("/api/v1/equipment")
async def list_equipment():
    """List equipment inventory"""
    equipment = [
        {
            "equipment_id": "EQ-001",
            "name": "Solar Simulator",
            "status": "Operational",
            "last_calibration": "2024-10-15",
            "next_calibration": "2025-10-15"
        },
        {
            "equipment_id": "EQ-002",
            "name": "I-V Curve Tracer",
            "status": "Operational",
            "last_calibration": "2024-09-20",
            "next_calibration": "2025-09-20"
        }
    ]
    return {"equipment": equipment, "count": len(equipment)}


@app.post("/api/v1/tests")
async def create_test(test_data: dict):
    """Create new test"""
    # Mock implementation - replace with actual database operations
    return {
        "message": "Test created successfully",
        "test_id": f"PV-2024-{1248}",
        "status": "created"
    }


@app.get("/api/v1/reports/{test_id}")
async def get_report(test_id: str):
    """Get test report"""
    # Mock implementation
    return {
        "test_id": test_id,
        "protocol": "IEC 61215",
        "status": "Approved",
        "report_url": f"/reports/{test_id}.pdf"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
