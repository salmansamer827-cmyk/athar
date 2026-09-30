from fastapi import APIRouter, HTTPException

from api.schemas.quant import (
    QuantAnalyzeRequest,
)

from api.services.quant_service import (
    QuantService,
)


router = APIRouter(
    prefix="/api/v1/quant",
    tags=["Quant"],
)

service = QuantService()


@router.post("/analyze")
def analyze(
    request: QuantAnalyzeRequest,
):
    try:
        return service.analyze(request)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "ERROR",
                "error": "QUANT_VALIDATION_ERROR",
                "message": str(exc),
            },
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "ERROR",
                "error": "INTERNAL_SERVER_ERROR",
                "message": str(exc),
            },
        )
