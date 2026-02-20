"""Agent configuration, templates, and prompt management."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentPersonality(str, Enum):
    """Pre-defined agent personalities."""
    
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    TECHNICAL = "technical"
    CASUAL = "casual"
    EMPATHETIC = "empathetic"
    ENTHUSIASTIC = "enthusiastic"


class BusinessCategory(str, Enum):
    """Business categories for template selection."""
    
    ECOMMERCE = "ecommerce"
    SAAS = "saas"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    FINANCE = "finance"
    LEGAL = "legal"
    HOSPITALITY = "hospitality"
    REAL_ESTATE = "real_estate"
    RESTAURANT = "restaurant"
    CONSULTING = "consulting"
    CUSTOM = "custom"


class ResponseTone(str, Enum):
    """Response tone options."""
    
    FORMAL = "formal"
    CONVERSATIONAL = "conversational"
    CONCISE = "concise"
    DETAILED = "detailed"


class ContentFilter(BaseModel):
    """Content filtering rules."""
    
    block_profanity: bool = True
    block_personal_info_requests: bool = True
    block_competitor_mentions: bool = False
    block_pricing_outside_context: bool = False
    require_business_context: bool = True
    max_response_length: int = 500
    allowed_topics: list[str] = []
    blocked_topics: list[str] = []


class AgentRestrictions(BaseModel):
    """Agent behavioral restrictions."""
    
    cannot_make_purchases: bool = True
    cannot_modify_account: bool = True
    cannot_access_personal_data: bool = True
    must_stay_on_topic: bool = True
    must_cite_sources: bool = False
    must_admit_uncertainty: bool = True
    can_refuse_inappropriate: bool = True
    require_human_handoff: list[str] = Field(
        default_factory=lambda: ["refund", "complaint", "legal"]
    )


class AgentTemplate(BaseModel):
    """Complete agent configuration template."""
    
    name: str
    category: BusinessCategory
    personality: AgentPersonality
    system_prompt: str
    welcome_message: str
    fallback_responses: dict[str, str]
    sample_questions: list[str]
    response_tone: ResponseTone
    content_filter: ContentFilter
    restrictions: AgentRestrictions


# Pre-defined templates
AGENT_TEMPLATES: dict[BusinessCategory, AgentTemplate] = {
    BusinessCategory.ECOMMERCE: AgentTemplate(
        name="E-commerce Assistant",
        category=BusinessCategory.ECOMMERCE,
        personality=AgentPersonality.FRIENDLY,
        system_prompt="""You are a helpful e-commerce customer service assistant.
Your role is to help customers with:
- Product information and specifications
- Order tracking and shipping
- Return and refund policies
- Product recommendations
- General shopping assistance

Always be friendly, patient, and solution-oriented.
If you don't have specific information, guide customers to contact support.
Never make promises about refunds or order changes - direct to human support.""",
        welcome_message="Hi! 👋 Welcome to our store! I'm here to help you find products, track orders, or answer any questions. What can I help you with today?",
        fallback_responses={
            "no_context": "I don't have that specific information right now. Let me connect you with our support team who can help better!",
            "off_topic": "I'm here to help with shopping and orders. For other inquiries, please visit our contact page.",
            "need_human": "This requires personal attention from our team. Please reach out to support@company.com or call us at [phone].",
        },
        sample_questions=[
            "What's your return policy?",
            "Do you ship internationally?",
            "How do I track my order?",
            "What payment methods do you accept?",
        ],
        response_tone=ResponseTone.CONVERSATIONAL,
        content_filter=ContentFilter(
            block_profanity=True,
            block_personal_info_requests=True,
            allowed_topics=["products", "shipping", "returns", "orders"],
            blocked_topics=["politics", "religion"],
        ),
        restrictions=AgentRestrictions(
            require_human_handoff=["refund", "complaint", "damaged_product", "warranty"],
        ),
    ),
    
    BusinessCategory.SAAS: AgentTemplate(
        name="SaaS Support Bot",
        category=BusinessCategory.SAAS,
        personality=AgentPersonality.TECHNICAL,
        system_prompt="""You are a technical support assistant for a SaaS platform.
Your role is to help users with:
- Feature explanations and how-tos
- Troubleshooting common issues
- Account and billing questions
- Integration setup
- Best practices

Be clear, concise, and technical when needed.
Provide step-by-step guidance.
If the issue requires technical investigation, escalate to support.""",
        welcome_message="Hello! I'm your technical assistant. I can help you with features, troubleshooting, and getting the most out of our platform. What do you need help with?",
        fallback_responses={
            "no_context": "I don't have information on that specific issue. Please submit a support ticket for personalized assistance.",
            "technical_issue": "This might require deeper technical investigation. I recommend contacting our technical support team.",
            "billing": "For billing and subscription changes, please contact billing@company.com or visit your account settings.",
        },
        sample_questions=[
            "How do I integrate with Slack?",
            "What's included in the Pro plan?",
            "How do I reset my password?",
            "Can I export my data?",
        ],
        response_tone=ResponseTone.DETAILED,
        content_filter=ContentFilter(
            block_profanity=True,
            allowed_topics=["features", "billing", "integrations", "troubleshooting"],
            require_business_context=True,
        ),
        restrictions=AgentRestrictions(
            cannot_modify_account=True,
            must_cite_sources=True,
            require_human_handoff=["billing_dispute", "account_deletion", "data_breach"],
        ),
    ),
    
    BusinessCategory.HEALTHCARE: AgentTemplate(
        name="Healthcare Support Assistant",
        category=BusinessCategory.HEALTHCARE,
        personality=AgentPersonality.EMPATHETIC,
        system_prompt="""You are a compassionate healthcare assistant.
Your role is to help with:
- Appointment scheduling information
- General facility information
- Insurance and billing questions
- Directions and hours

IMPORTANT: You cannot provide medical advice.
Be empathetic and professional.
For medical questions, always recommend consulting healthcare providers.""",
        welcome_message="Hello, I'm here to help with appointments, facility information, and general questions. How can I assist you today?",
        fallback_responses={
            "medical_advice": "I cannot provide medical advice. Please contact your healthcare provider or call our office for medical questions.",
            "emergency": "If this is a medical emergency, please call 911 or go to the nearest emergency room immediately.",
            "insurance": "For specific insurance questions, please contact our billing department at [phone].",
        },
        sample_questions=[
            "What are your office hours?",
            "Do you accept my insurance?",
            "How do I schedule an appointment?",
            "Where are you located?",
        ],
        response_tone=ResponseTone.FORMAL,
        content_filter=ContentFilter(
            block_profanity=True,
            block_personal_info_requests=True,
            allowed_topics=["appointments", "insurance", "location", "hours"],
            blocked_topics=["medical_advice", "diagnosis", "treatment"],
            max_response_length=300,
        ),
        restrictions=AgentRestrictions(
            cannot_make_purchases=True,
            cannot_access_personal_data=True,
            must_admit_uncertainty=True,
            require_human_handoff=["medical_emergency", "diagnosis", "prescription"],
        ),
    ),
    
    BusinessCategory.EDUCATION: AgentTemplate(
        name="Education Support Bot",
        category=BusinessCategory.EDUCATION,
        personality=AgentPersonality.ENTHUSIASTIC,
        system_prompt="""You are an enthusiastic educational assistant.
Your role is to help with:
- Course information and curriculum
- Admission and enrollment
- Campus facilities and events
- Academic support resources

Be encouraging and informative.
Inspire learning and growth.
Guide students to appropriate resources.""",
        welcome_message="Welcome! 🎓 I'm here to help you with courses, admissions, and campus information. What would you like to know?",
        fallback_responses={
            "admissions": "For specific admissions questions, please contact admissions@school.edu",
            "grades": "For grade inquiries, please log into your student portal or contact your instructor.",
            "financial_aid": "For financial aid questions, visit our financial aid office or call [phone].",
        },
        sample_questions=[
            "What programs do you offer?",
            "How do I apply?",
            "What are the admission requirements?",
            "Do you offer online courses?",
        ],
        response_tone=ResponseTone.CONVERSATIONAL,
        content_filter=ContentFilter(
            block_profanity=True,
            allowed_topics=["courses", "admissions", "campus", "events"],
        ),
        restrictions=AgentRestrictions(
            cannot_access_personal_data=True,
            require_human_handoff=["grade_dispute", "academic_integrity", "appeals"],
        ),
    ),
    
    BusinessCategory.RESTAURANT: AgentTemplate(
        name="Restaurant Assistant",
        category=BusinessCategory.RESTAURANT,
        personality=AgentPersonality.FRIENDLY,
        system_prompt="""You are a friendly restaurant assistant.
Your role is to help with:
- Menu information and specials
- Reservations and hours
- Dietary accommodations
- Location and parking

Be warm and inviting.
Make guests feel welcome.
Help them have a great dining experience.""",
        welcome_message="Welcome! 🍽️ I'm here to help with menu questions, reservations, and anything else. What can I help you with?",
        fallback_responses={
            "reservations": "To make a reservation, please call us at [phone] or use our online booking system.",
            "private_events": "For private events and catering, please contact events@restaurant.com",
            "complaints": "We're sorry to hear that. Please speak with our manager or email feedback@restaurant.com",
        },
        sample_questions=[
            "What's on the menu?",
            "Do you have vegetarian options?",
            "What are your hours?",
            "Do you take reservations?",
        ],
        response_tone=ResponseTone.CONVERSATIONAL,
        content_filter=ContentFilter(
            allowed_topics=["menu", "reservations", "hours", "location", "dietary"],
        ),
        restrictions=AgentRestrictions(
            require_human_handoff=["complaint", "food_safety", "allergic_reaction"],
        ),
    ),
}


class PromptAssistant:
    """AI-powered assistant to help users write better prompts."""
    
    IMPROVEMENT_TEMPLATES = {
        "too_vague": """Your prompt could be more specific. Consider:
- What specific role should the AI play?
- What topics should it focus on?
- What tone should it use?
- What should it avoid?""",
        
        "too_long": """Your prompt is quite long. Consider:
- Focus on the most important guidelines
- Use bullet points for clarity
- Separate instructions from examples""",
        
        "missing_context": """Add more context about:
- Your business type and industry
- Your target audience
- Common customer questions
- Your brand voice""",
        
        "good": """Your prompt looks good! It includes:
✓ Clear role definition
✓ Specific instructions
✓ Appropriate constraints
✓ Tone guidance""",
    }
    
    @staticmethod
    def analyze_prompt(prompt: str) -> dict[str, Any]:
        """Analyze a user's prompt and provide feedback."""
        issues = []
        suggestions = []
        score = 10
        
        # Check length
        word_count = len(prompt.split())
        if word_count < 20:
            issues.append("too_short")
            suggestions.append("Add more detail about the AI's role and behavior")
            score -= 3
        elif word_count > 500:
            issues.append("too_long")
            suggestions.append("Consider shortening and focusing on key points")
            score -= 1
        
        # Check for key elements
        has_role = any(word in prompt.lower() for word in ["you are", "act as", "role"])
        has_constraints = any(word in prompt.lower() for word in ["don't", "cannot", "avoid", "never"])
        has_tone = any(word in prompt.lower() for word in ["friendly", "professional", "casual", "formal"])
        
        if not has_role:
            issues.append("missing_role")
            suggestions.append("Start with 'You are a [role]' to define the AI's character")
            score -= 2
        
        if not has_constraints:
            issues.append("missing_constraints")
            suggestions.append("Add guidelines about what the AI should NOT do")
            score -= 1
        
        if not has_tone:
            issues.append("missing_tone")
            suggestions.append("Specify the tone (e.g., friendly, professional)")
            score -= 1
        
        # Overall assessment
        if score >= 8:
            quality = "excellent"
        elif score >= 6:
            quality = "good"
        elif score >= 4:
            quality = "needs_improvement"
        else:
            quality = "poor"
        
        return {
            "score": score,
            "quality": quality,
            "issues": issues,
            "suggestions": suggestions,
            "word_count": word_count,
        }
    
    @staticmethod
    def improve_prompt(rough_prompt: str, business_type: str = "general") -> str:
        """Improve a rough prompt into a production-ready system prompt."""
        
        # This is a simple template-based improvement
        # In production, this could use an LLM
        
        template = f"""You are a helpful customer service assistant for a {business_type} business.

Based on the user's intent: "{rough_prompt}"

Your responsibilities:
- Answer customer questions accurately and helpfully
- Be friendly and professional
- Use the provided context to give accurate information
- Admit when you don't know something

Guidelines:
- Always be polite and patient
- Keep responses concise but complete
- If you can't help, direct customers to human support
- Never make promises you can't keep
- Stay focused on business-related topics

Response style:
- Use clear, simple language
- Be conversational but professional
- Match the customer's tone
- Use formatting for readability when needed"""
        
        return template
    
    @staticmethod
    def generate_welcome_messages(business_name: str, category: BusinessCategory) -> list[str]:
        """Generate welcome message suggestions."""
        
        templates = {
            BusinessCategory.ECOMMERCE: [
                f"Hi! 👋 Welcome to {business_name}! I'm here to help you shop. What are you looking for?",
                f"Hello! Thanks for visiting {business_name}. How can I assist you today?",
                f"Welcome! I'm your shopping assistant. Feel free to ask about products, orders, or anything else!",
            ],
            BusinessCategory.SAAS: [
                f"Hello! Welcome to {business_name}. I can help with features, setup, and troubleshooting. What do you need?",
                f"Hi there! I'm your {business_name} assistant. How can I help you get the most out of our platform?",
                f"Welcome! Need help with {business_name}? I'm here to assist with any questions.",
            ],
            BusinessCategory.HEALTHCARE: [
                f"Hello, welcome to {business_name}. I can help with appointments and facility information. How may I assist you?",
                f"Welcome to {business_name}. How can I help you today?",
                f"Hello! I'm here to help with scheduling and general information. What do you need?",
            ],
        }
        
        return templates.get(category, [
            f"Hello! Welcome to {business_name}. How can I help you today?",
            f"Hi! I'm here to assist with your questions about {business_name}. What would you like to know?",
            f"Welcome! I'm your {business_name} assistant. Feel free to ask me anything!",
        ])
    
    @staticmethod
    def get_sample_prompts(category: BusinessCategory) -> list[str]:
        """Get sample prompts for a business category."""
        
        samples = {
            BusinessCategory.ECOMMERCE: [
                "You are a friendly e-commerce assistant. Help customers find products, track orders, and answer questions about our store policies.",
                "Act as a product expert. Help customers with product recommendations, specifications, and comparisons. Be enthusiastic but honest.",
            ],
            BusinessCategory.SAAS: [
                "You are a technical support specialist. Help users troubleshoot issues, understand features, and integrate our platform.",
                "Act as a customer success assistant. Guide users to get maximum value from our software with clear explanations.",
            ],
            BusinessCategory.CONSULTING: [
                "You are a professional consulting assistant. Answer questions about our services, methodology, and how we can help clients.",
                "Act as a business advisor's assistant. Help potential clients understand our expertise and process.",
            ],
        }
        
        return samples.get(category, [
            "You are a helpful customer service assistant. Answer questions based on the provided information.",
        ])


def get_template(category: BusinessCategory) -> AgentTemplate:
    """Get template for a business category."""
    return AGENT_TEMPLATES.get(category, AGENT_TEMPLATES[BusinessCategory.ECOMMERCE])


def customize_template(
    template: AgentTemplate,
    business_name: str,
    custom_guidelines: str = None,
) -> AgentTemplate:
    """Customize a template for specific business."""
    
    # Replace placeholders
    system_prompt = template.system_prompt
    if custom_guidelines:
        system_prompt += f"\n\nAdditional Guidelines:\n{custom_guidelines}"
    
    welcome = template.welcome_message.replace("our store", business_name)
    welcome = welcome.replace("our platform", business_name)
    
    return AgentTemplate(
        name=f"{business_name} Assistant",
        category=template.category,
        personality=template.personality,
        system_prompt=system_prompt,
        welcome_message=welcome,
        fallback_responses=template.fallback_responses,
        sample_questions=template.sample_questions,
        response_tone=template.response_tone,
        content_filter=template.content_filter,
        restrictions=template.restrictions,
    )


def validate_response_against_filters(
    response: str,
    filters: ContentFilter,
) -> tuple[bool, str]:
    """
    Validate AI response against content filters.
    
    Returns:
        tuple: (is_valid, reason)
    """
    import re
    
    # Check length
    if len(response) > filters.max_response_length:
        return False, "response_too_long"
    
    # Check profanity (basic check)
    if filters.block_profanity:
        profanity_patterns = [
            r'\b(damn|hell|crap)\b',  # Add actual profanity list
        ]
        for pattern in profanity_patterns:
            if re.search(pattern, response.lower()):
                return False, "contains_profanity"
    
    # Check for blocked topics
    for topic in filters.blocked_topics:
        if topic.lower() in response.lower():
            return False, f"blocked_topic: {topic}"
    
    return True, "valid"
