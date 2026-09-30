# Azure VNet API

A simple Python FastAPI application that:

1. Authenticates users using Microsoft Entra ID.
2. Creates an Azure VNet with multiple subnets.
3. Stores the created-resource information in a JSON file.
4. Allows authenticated users to retrieve the stored VNet information.


---

## Architecture

```text
Client
  |
  | Bearer token
  v
FastAPI
  |
  +---- Microsoft Entra ID
  |
  +---- Azure Network SDK
  |          |
  |          +---- VNet
  |          +---- Subnets
  |
  +---- data/vnets.json
             |
             +---- Stored VNet information
```

---

## Project structure

```text
azure-vnet-api/
│
├── app/
│   ├── __init__.py
│   ├── auth.py
│   ├── main.py
│   └── models.py
│
├── data/
│   └── vnets.json
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

# 1. Prerequisites

You need:

- Python 3.10+
- An Azure subscription
- Azure CLI
- A Microsoft Entra ID App Registration

The VNet itself does not need to exist beforehand. The API creates it.

---

# 2. Azure permissions

The Azure identity used to run the API needs permission to create VNets and subnets.

For local development, you can use your Azure CLI identity.

After logging in:

```bash
az login
```

Select the correct subscription:

```bash
az account set --subscription <subscription-id>
```

Assign `Network Contributor` to your user at the resource-group level if needed:

```bash
az role assignment create   --assignee <your-user-or-service-principal>   --role "Network Contributor"   --scope /subscriptions/<subscription-id>/resourceGroups/<resource-group-name>
```

---

# 3. Microsoft Entra ID authentication

Create an App Registration in:

**Azure Portal → Microsoft Entra ID → App registrations**

Create an application such as:

```text
Azure VNet API
```

Copy:

- Tenant ID
- Application/Client ID

The API validates that the access token:

- Has a valid Microsoft signature
- Was issued by the configured tenant
- Is intended for this application
- Has not expired

There is no application-specific authorization hierarchy. Any user with a valid access token can use the resource endpoints.

---

# 4. Environment variables

Copy:

```bash
cp .env.example .env
```

Set:

```env
AZURE_TENANT_ID=<tenant-id>
AZURE_CLIENT_ID=<api-app-registration-client-id>
AZURE_SUBSCRIPTION_ID=<subscription-id>
```

Do not commit `.env` to GitHub.

---

# 5. Install dependencies

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it.

macOS/Linux:

```bash
source .venv/bin/activate
```

Windows:

```powershell
.venv\Scripts\activate
```

Install packages:

```bash
pip install -r requirements.txt
```

---

# 6. Login to Azure

The application uses `DefaultAzureCredential`.

For local development:

```bash
az login
```

The Azure SDK will use the Azure CLI credentials.

---

# 7. Start the API

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://localhost:8000
```

Swagger documentation:

```text
http://localhost:8000/docs
```

---

# 8. API endpoints

## Health check

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

This endpoint does not require authentication.

---

## Create a VNet

```http
POST /vnets
Authorization: Bearer <access-token>
Content-Type: application/json
```

Request:

```json
{
  "name": "challenge-vnet",
  "resource_group": "azure-vnet-api-rg",
  "location": "westeurope",
  "address_space": [
    "10.10.0.0/16"
  ],
  "subnets": [
    {
      "name": "app-subnet",
      "address_prefix": "10.10.1.0/24"
    },
    {
      "name": "data-subnet",
      "address_prefix": "10.10.2.0/24"
    },
    {
      "name": "management-subnet",
      "address_prefix": "10.10.3.0/24"
    }
  ]
}
```

The API:

1. Creates the VNet.
2. Creates each subnet.
3. Stores the result in `data/vnets.json`.
4. Returns the created resource information.

---

## Get all VNets

```http
GET /vnets
Authorization: Bearer <access-token>
```

The API reads `data/vnets.json` and returns the stored resources.

Example:

```json
[
  {
    "id": "/subscriptions/.../virtualNetworks/challenge-vnet",
    "name": "challenge-vnet",
    "resource_group": "azure-vnet-api-rg",
    "location": "westeurope",
    "address_space": [
      "10.10.0.0/16"
    ],
    "subnets": [
      {
        "name": "app-subnet",
        "address_prefix": "10.10.1.0/24"
      },
      {
        "name": "data-subnet",
        "address_prefix": "10.10.2.0/24"
      },
      {
        "name": "management-subnet",
        "address_prefix": "10.10.3.0/24"
      }
    ]
  }
]
```

---

## Get one VNet

```http
GET /vnets/challenge-vnet
Authorization: Bearer <access-token>
```

If the VNet is not present in the JSON file:

```http
404 Not Found
```

---

# 9. Authentication

The resource endpoints require:

```http
Authorization: Bearer <access-token>
```

Without a valid token:

```http
401 Unauthorized
```

Authentication is handled by Microsoft Entra ID.

Once a user has a valid access token, the API does not apply additional user-specific authorization. This matches the requirement that authorization is open to all authenticated users.

---

# 10. Getting an access token

Postman can be used to obtain an OAuth 2.0 access token from Microsoft Entra ID.

Configure the Microsoft identity platform authorization and token endpoints using the App Registration created earlier.

Then send the returned token as:

```http
Authorization: Bearer <access-token>
```