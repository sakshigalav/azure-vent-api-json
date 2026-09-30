import json
import os
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException

from azure.identity import DefaultAzureCredential
from azure.mgmt.network import NetworkManagementClient

from .auth import authenticate
from .models import VNetRequest, VNetResponse


app = FastAPI(
    title="Azure VNet API",
    description="Simple API for creating and retrieving Azure VNets and subnets.",
    version="1.0.0",
)

# Azure client
credential = DefaultAzureCredential()
subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
network_client = NetworkManagementClient(credential, subscription_id)

# JSON file used to store the created resource information.
DATA_FILE = Path(__file__).parent.parent / "data" / "vnets.json"


def read_vnets():
    if not DATA_FILE.exists():
        return []

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_vnets(vnets):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(vnets, file, indent=2)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/vnets", response_model=VNetResponse)
def create_vnet(
    request: VNetRequest,
    user=Depends(authenticate),
):
    # Create the VNet.
    vnet = network_client.virtual_networks.begin_create_or_update(
        request.resource_group,
        request.name,
        {
            "location": request.location,
            "address_space": {
                "address_prefixes": request.address_space
            },
        },
    ).result()

    # Create each subnet.
    for subnet in request.subnets:
        network_client.subnets.begin_create_or_update(
            request.resource_group,
            request.name,
            subnet.name,
            {
                "address_prefix": subnet.address_prefix,
            },
        ).result()

    result = {
        "id": vnet.id,
        "name": vnet.name,
        "resource_group": request.resource_group,
        "location": request.location,
        "address_space": request.address_space,
        "subnets": [
            {
                "name": subnet.name,
                "address_prefix": subnet.address_prefix,
            }
            for subnet in request.subnets
        ],
    }

    # Store the result in the JSON file.
    vnets = read_vnets()

    # Replace an existing entry with the same VNet name.
    vnets = [item for item in vnets if item["name"] != result["name"]]
    vnets.append(result)

    save_vnets(vnets)

    return result


@app.get("/vnets", response_model=list[VNetResponse])
def list_vnets(user=Depends(authenticate)):
    return read_vnets()


@app.get("/vnets/{name}", response_model=VNetResponse)
def get_single_vnet(
    name: str,
    user=Depends(authenticate),
):
    vnets = read_vnets()

    for vnet in vnets:
        if vnet["name"] == name:
            return vnet

    raise HTTPException(
        status_code=404,
        detail="VNet not found",
    )
