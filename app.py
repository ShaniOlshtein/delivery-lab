from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()

 
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": str(exc.detail)}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid request"}
    )

deliveries = {}
next_id = 1


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/deliveries", status_code=201)
async def create_delivery(request: Request):
    global next_id

    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Body must be a JSON object")

    recipient = data.get("recipient")
    address = data.get("address")

    if not isinstance(recipient, str) or not recipient.strip():
        raise HTTPException(status_code=400, detail="Invalid recipient")

    if not isinstance(address, str) or not address.strip():
        raise HTTPException(status_code=400, detail="Invalid address")

    delivery = {
        "id": next_id,
        "recipient": recipient,
        "address": address,
        "status": "created"
    }

    deliveries[next_id] = delivery
    next_id += 1

    return delivery
VALID_STATUSES = {"created", "in_transit", "delivered"}


@app.get("/deliveries")
def get_deliveries(status: str = None):
    if status is not None and status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")

    result = list(deliveries.values())

    if status is not None:
        result = [delivery for delivery in result if delivery["status"] == status]

    return result
 
@app.get("/deliveries/{delivery_id}")
def get_delivery(delivery_id: int):
    delivery = deliveries.get(delivery_id)

    if delivery is None:
        raise HTTPException(status_code=404, detail="Delivery not found")

    return delivery
STATUS_ORDER = ["created", "in_transit", "delivered"]


@app.patch("/deliveries/{delivery_id}/status")
async def update_delivery_status(delivery_id: int, request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Body must be a JSON object")

    status = data.get("status")

    if not isinstance(status, str) or status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")

    delivery = deliveries.get(delivery_id)

    if delivery is None:
        raise HTTPException(status_code=404, detail="Delivery not found")

    current_index = STATUS_ORDER.index(delivery["status"])
    new_index = STATUS_ORDER.index(status)

    if new_index != current_index + 1:
        raise HTTPException(status_code=409, detail="Invalid status transition")

    delivery["status"] = status
    return delivery
from fastapi import Response


@app.delete("/deliveries/{delivery_id}", status_code=204)
def delete_delivery(delivery_id: int):
    delivery = deliveries.get(delivery_id)

    if delivery is None:
        raise HTTPException(status_code=404, detail="Delivery not found")

    if delivery["status"] != "created":
        raise HTTPException(status_code=409, detail="Only created deliveries can be deleted")

    del deliveries[delivery_id]

    return Response(status_code=204)
