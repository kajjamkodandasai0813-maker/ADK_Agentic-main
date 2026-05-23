"""
tools/search_tools.py - Simulated web search tools for company/job research
In production, replace with real APIs: SerpAPI, Google Search API, LinkedIn API, etc.
"""

import json
from typing import Optional


# ─────────────────────────────────────────────────────────────────
# Simulated knowledge base (replace with real API calls in prod)
# ─────────────────────────────────────────────────────────────────

COMPANY_DATABASE = {
    "google": {
        "name": "Google LLC (Alphabet Inc.)",
        "industry": "Technology / Cloud / AI",
        "founded": 1998,
        "headquarters": "Mountain View, California",
        "size": "180,000+ employees",
        "culture": "Innovation-driven, data-centric, 20% time philosophy, OKR framework",
        "mission": "Organize the world's information and make it universally accessible and useful",
        "products": ["Search", "Gmail", "Google Cloud", "Android", "YouTube", "Gemini AI"],
        "tech_stack": ["Python", "Go", "Java", "C++", "Kubernetes", "TensorFlow"],
        "values": ["Focus on the user", "Think big", "Move fast", "Be transparent"],
        "glassdoor_rating": 4.3,
        "interview_style": "Behavioral + Technical + System Design (STAR format)",
        "recent_news": "Heavy investment in Gemini AI, Google Cloud growth, quantum computing research",
    },
    "amazon": {
        "name": "Amazon.com Inc.",
        "industry": "E-commerce / Cloud / Logistics",
        "founded": 1994,
        "headquarters": "Seattle, Washington",
        "size": "1,500,000+ employees",
        "culture": "Customer obsession, ownership, bias for action, 16 leadership principles",
        "mission": "To be Earth's most customer-centric company",
        "products": ["AWS", "Prime", "Alexa", "Kindle", "Fulfillment by Amazon"],
        "tech_stack": ["Java", "Python", "AWS", "DynamoDB", "Spark", "Kafka"],
        "values": ["Customer Obsession", "Ownership", "Invent and Simplify", "Think Big"],
        "glassdoor_rating": 3.8,
        "interview_style": "Leadership Principles-based behavioral + technical (LP stories critical)",
        "recent_news": "AWS re:Invent AI announcements, Alexa AI upgrade, robot warehouse expansion",
    },
    "microsoft": {
        "name": "Microsoft Corporation",
        "industry": "Technology / Cloud / Productivity",
        "founded": 1975,
        "headquarters": "Redmond, Washington",
        "size": "220,000+ employees",
        "culture": "Growth mindset, inclusive design, one Microsoft philosophy",
        "mission": "Empower every person and every organization on the planet to achieve more",
        "products": ["Azure", "Office 365", "Windows", "GitHub", "LinkedIn", "Copilot"],
        "tech_stack": ["C#", ".NET", "TypeScript", "Python", "Azure", "Cosmos DB"],
        "values": ["Respect", "Integrity", "Accountability"],
        "glassdoor_rating": 4.4,
        "interview_style": "Behavioral (growth mindset) + coding + design",
        "recent_news": "OpenAI partnership, Copilot integration across products, Azure AI expansion",
    },
}

SALARY_DATABASE = {
    "software engineer": {
        "entry": {"min": 85000, "max": 120000, "currency": "USD"},
        "mid": {"min": 120000, "max": 180000, "currency": "USD"},
        "senior": {"min": 180000, "max": 280000, "currency": "USD"},
        "staff": {"min": 250000, "max": 400000, "currency": "USD"},
    },
    "data scientist": {
        "entry": {"min": 80000, "max": 115000, "currency": "USD"},
        "mid": {"min": 115000, "max": 165000, "currency": "USD"},
        "senior": {"min": 165000, "max": 250000, "currency": "USD"},
    },
    "product manager": {
        "entry": {"min": 90000, "max": 130000, "currency": "USD"},
        "mid": {"min": 130000, "max": 190000, "currency": "USD"},
        "senior": {"min": 190000, "max": 300000, "currency": "USD"},
    },
    "machine learning engineer": {
        "entry": {"min": 100000, "max": 145000, "currency": "USD"},
        "mid": {"min": 145000, "max": 210000, "currency": "USD"},
        "senior": {"min": 200000, "max": 320000, "currency": "USD"},
    },
    "devops engineer": {
        "entry": {"min": 80000, "max": 110000, "currency": "USD"},
        "mid": {"min": 110000, "max": 160000, "currency": "USD"},
        "senior": {"min": 155000, "max": 230000, "currency": "USD"},
    },
}

JOB_TRENDS = {
    "ai_ml": {
        "trend": "Explosive growth",
        "top_skills": ["Python", "PyTorch", "LLMs", "MLOps", "RAG", "Agent frameworks"],
        "yoy_growth": "35%",
        "hot_roles": ["ML Engineer", "AI Engineer", "Prompt Engineer", "AI Safety Researcher"],
    },
    "cloud": {
        "trend": "Strong growth",
        "top_skills": ["AWS", "Azure", "GCP", "Terraform", "Kubernetes", "Docker"],
        "yoy_growth": "22%",
        "hot_roles": ["Cloud Architect", "Site Reliability Engineer", "Platform Engineer"],
    },
    "fullstack": {
        "trend": "Stable",
        "top_skills": ["React", "Node.js", "TypeScript", "PostgreSQL", "GraphQL"],
        "yoy_growth": "8%",
        "hot_roles": ["Full Stack Engineer", "Frontend Engineer", "API Developer"],
    },
}


def search_company_info(company_name: str) -> dict:
    """
    Search for company information to help personalize job applications.

    Args:
        company_name: Name of the company to research

    Returns:
        dict with company details, culture, values, interview style
    """
    key = company_name.lower().strip()

    # Check local database first
    for db_key, data in COMPANY_DATABASE.items():
        if db_key in key or key in db_key:
            return {
                "success": True,
                "found": True,
                "company": data,
                "source": "knowledge_base",
                "note": "In production, this would call a real search API",
            }

    # Return generic template if not found
    return {
        "success": True,
        "found": False,
        "company": {
            "name": company_name,
            "industry": "Research required",
            "culture": "Visit company website and LinkedIn for culture insights",
            "values": "Check company 'About Us' and 'Mission' pages",
            "interview_style": "Prepare STAR format behavioral answers + role-specific technical prep",
            "recent_news": f"Search '{company_name} news 2026' for latest updates",
            "recommendation": "Personalize heavily based on their recent announcements",
        },
        "source": "generic_template",
        "note": "Company not in knowledge base. In production, this queries real-time web search APIs",
    }


def search_job_market_trends(domain: str) -> dict:
    """
    Search for current job market trends in a specific domain.

    Args:
        domain: Job domain (e.g., 'ai_ml', 'cloud', 'fullstack')

    Returns:
        dict with market trends, top skills, hot roles, growth data
    """
    key = domain.lower().replace(" ", "_").replace("-", "_")

    # Fuzzy match
    for trend_key, data in JOB_TRENDS.items():
        if trend_key in key or key in trend_key:
            return {
                "success": True,
                "domain": domain,
                "trends": data,
                "timestamp": "2026-03-30",
                "note": "In production, this queries LinkedIn, Glassdoor, and job board APIs",
            }

    return {
        "success": True,
        "domain": domain,
        "trends": {
            "trend": "Consult LinkedIn Insights and Glassdoor for real-time data",
            "top_skills": ["Problem solving", "Communication", "Domain expertise"],
            "yoy_growth": "Varies by location and specialization",
            "hot_roles": ["Senior roles with AI integration experience are in demand"],
        },
        "note": "Domain not in knowledge base — real API would return live market data",
    }


def search_salary_data(role: str, level: str = "mid") -> dict:
    """
    Search for salary benchmarks for a given role and experience level.

    Args:
        role: Job role (e.g., 'software engineer', 'data scientist')
        level: Experience level — 'entry', 'mid', 'senior', 'staff'

    Returns:
        dict with salary range and negotiation tips
    """
    role_key = role.lower().strip()
    level_key = level.lower().strip()

    for db_role, levels in SALARY_DATABASE.items():
        if db_role in role_key or role_key in db_role:
            salary_info = levels.get(level_key, levels.get("mid", {}))
            return {
                "success": True,
                "role": role,
                "level": level_key,
                "salary_range": salary_info,
                "negotiation_tips": [
                    "Always negotiate — 70% of employers expect it",
                    "Lead with market data, not personal need",
                    f"Target upper quartile: ${salary_info.get('max', 0):,}",
                    "Consider total comp: base, equity, bonus, benefits",
                    "Get competing offers if possible for leverage",
                ],
                "source": "salary_database_2026",
                "note": "In production, queries Levels.fyi, Glassdoor, and LinkedIn Salary APIs",
            }

    return {
        "success": True,
        "role": role,
        "level": level_key,
        "salary_range": {"note": "Use Levels.fyi, Glassdoor, or LinkedIn Salary for this role"},
        "negotiation_tips": [
            "Research role-specific data on Levels.fyi",
            "Network with people in the role for real numbers",
            "Always negotiate — it signals confidence",
        ],
        "note": "Role not in local database",
    }
