import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# --------------------------------------------------------------------
# Gemini Configuration
# --------------------------------------------------------------------

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found in .env")

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

client = genai.Client(api_key=API_KEY)

# --------------------------------------------------------------------
# System Prompt
# --------------------------------------------------------------------

SYSTEM_PROMPT = """
You are a Senior Azure Cloud Cost Optimization Consultant with deep expertise
in Azure architecture, Azure Advisor recommendations, FinOps, and Microsoft
Well-Architected Framework.

Your job is to analyze Azure resources and identify opportunities to reduce
monthly Azure spending without impacting production workloads.

Analyze every supplied resource and look for:

• Idle Virtual Machines
• Deallocated VMs still consuming resources
• Oversized VM SKUs
• Low CPU utilization opportunities
• Missing Reserved Instance opportunities
• Missing Savings Plan opportunities
• Premium SSDs that could use Standard SSD
• Unattached Managed Disks
• Orphaned Public IP Addresses
• Idle Load Balancers
• Under-utilized App Services
• Overprovisioned AKS clusters
• Unused Network Interfaces
• Storage optimization opportunities
• Missing Auto Shutdown
• Old snapshots
• Expensive SKUs
• Duplicate resources
• Cost optimization best practices

For every issue include:

- title
- resource_name
- severity (high | medium | low)
- description
- recommendation
- estimated_savings_usd
- fix_command (Azure CLI)

If there are no problems, return an empty issues array.

IMPORTANT:

Return ONLY valid JSON.

Never return markdown.

Never explain your reasoning.

Schema:

{
  "summary": "",
  "estimated_monthly_savings_usd": 0,
  "issues": [
    {
      "title": "",
      "resource_name": "",
      "severity": "high",
      "description": "",
      "recommendation": "",
      "estimated_savings_usd": 0,
      "fix_command": ""
    }
  ]
}
"""

# --------------------------------------------------------------------
# Analyzer
# --------------------------------------------------------------------


async def analyze_resources(resources):
    """
    Analyze Azure resources using Gemini and return structured
    optimization recommendations.
    """

    if not resources:
        return {
            "summary": "No Azure resources found.",
            "estimated_monthly_savings_usd": 0,
            "issues": []
        }

    prompt = f"""
Azure Resources:

{json.dumps(resources, indent=2)}
"""

    try:

        response = client.models.generate_content(
            model=MODEL,
            contents=[
                SYSTEM_PROMPT,
                prompt
            ],
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json"
            )
        )

        content = response.text.strip()

        result = json.loads(content)

        # Safety defaults
        result.setdefault("summary", "")
        result.setdefault("estimated_monthly_savings_usd", 0)
        result.setdefault("issues", [])

        return result

    except json.JSONDecodeError:

        return {
            "summary": "Gemini returned invalid JSON.",
            "estimated_monthly_savings_usd": 0,
            "issues": [],
            "raw_response": content
        }

    except Exception as e:

        return {
            "summary": "AI analysis failed.",
            "estimated_monthly_savings_usd": 0,
            "issues": [],
            "error": str(e)
        }