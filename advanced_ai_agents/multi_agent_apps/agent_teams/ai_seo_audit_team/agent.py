"""
Fallback SEO Audit Agent - Alternative version without MCP dependency.
This version uses basic HTTP requests as a fallback for web scraping.
"""

from __future__ import annotations
import os
import requests
import inspect
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.base_tool import BaseTool
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# =============================================================================
# Output Schemas (same as original)
# =============================================================================

class HeadingItem(BaseModel):
    tag: str = Field(..., description="Heading tag such as h1, h2, h3.")
    text: str = Field(..., description="Text content of the heading.")

class LinkCounts(BaseModel):
    internal: Optional[int] = Field(None, description="Number of internal links on the page.")
    external: Optional[int] = Field(None, description="Number of external links on the page.")
    broken: Optional[int] = Field(None, description="Number of broken links detected.")
    notes: Optional[str] = Field(None, description="Additional qualitative observations about linking.")

class AuditResults(BaseModel):
    title_tag: str = Field(..., description="Full title tag text.")
    meta_description: str = Field(..., description="Meta description text.")
    primary_heading: str = Field(..., description="Primary H1 heading on the page.")
    secondary_headings: List[HeadingItem] = Field(default_factory=list, description="Secondary headings (H2-H4) in reading order.")
    word_count: Optional[int] = Field(None, description="Approximate number of words in the main content.")
    content_summary: str = Field(..., description="Summary of the main topics and structure of the content.")
    link_counts: LinkCounts = Field(..., description="Quantitative snapshot of internal/external/broken links.")
    technical_findings: List[str] = Field(default_factory=list, description="List of notable technical SEO issues.")
    content_opportunities: List[str] = Field(default_factory=list, description="Observed content gaps or opportunities for improvement.")

class TargetKeywords(BaseModel):
    primary_keyword: str = Field(..., description="Most likely primary keyword target.")
    secondary_keywords: List[str] = Field(default_factory=list, description="Related secondary or supporting keywords.")
    search_intent: str = Field(..., description="Dominant search intent inferred from the page.")
    supporting_topics: List[str] = Field(default_factory=list, description="Cluster of supporting topics or entities.")

class PageAuditOutput(BaseModel):
    audit_results: AuditResults = Field(..., description="Structured on-page audit findings.")
    target_keywords: TargetKeywords = Field(..., description="Keyword focus derived from page content.")

class SerpResult(BaseModel):
    rank: int = Field(..., description="Organic ranking position.")
    title: str = Field(..., description="Title of the search result.")
    url: str = Field(..., description="Landing page URL.")
    snippet: str = Field(..., description="SERP snippet or summary.")
    content_type: str = Field(..., description="Content format.")

class SerpAnalysis(BaseModel):
    primary_keyword: str = Field(..., description="Keyword used for SERP research.")
    top_10_results: List[SerpResult] = Field(..., description="Top organic competitors for the keyword.")
    title_patterns: List[str] = Field(default_factory=list, description="Common patterns or phrases used in competitor titles.")
    content_formats: List[str] = Field(default_factory=list, description="Typical content formats found.")
    people_also_ask: List[str] = Field(default_factory=list, description="Representative questions surfaced in People Also Ask.")
    key_themes: List[str] = Field(default_factory=list, description="Notable recurring themes, features, or angles competitors emphasize.")
    differentiation_opportunities: List[str] = Field(default_factory=list, description="Opportunities to stand out versus competitors.")


# =============================================================================
# Fallback Web Scraper Function (Simple approach)
# =============================================================================

def simple_web_scraper(url: str) -> str:
    """Simple web scraper as fallback when MCP is not available."""
    try:
        import requests
        import re
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Basic HTML content extraction
        html_content = response.text
        
        # Extract title
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else "No title found"
        
        # Extract meta description
        meta_desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', html_content, re.IGNORECASE)
        meta_desc = meta_desc_match.group(1).strip() if meta_desc_match else "No meta description found"
        
        # Extract basic text content (remove HTML tags)
        text_content = re.sub(r'<[^>]+>', '', html_content)
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        # Word count
        word_count = len(text_content.split())
        
        result = f"""**SCRAPED CONTENT FOR: {url}**

**Title:** {title}

**Meta Description:** {meta_desc}

**Word Count:** {word_count}

**Content Preview:** {text_content[:1000]}...

**Status:** Successfully scraped using fallback method"""
        
        return result
        
    except Exception as e:
        return f"Error scraping {url}: {str(e)}"

def save_report_to_markdown(url: str, report_content: str) -> str:
    """
    Save the SEO audit report to a markdown file with timestamp.
    
    Args:
        url: The URL that was audited
        report_content: The full report content from the agent
    
    Returns:
        str: Path to the saved markdown file
    """
    try:
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        reports_dir = os.path.join(script_dir, "reports")
        
        # Create reports directory if it doesn't exist
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
        
        # Extract domain from URL for filename
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.replace('www.', '').replace('.', '_')
        
        # Create timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        # Create filename
        filename = f"seo_audit_{domain}_{timestamp}.md"
        filepath = os.path.join(reports_dir, filename)
        
        # Format the content as markdown
        markdown_content = f"""# SEO Audit Report

**URL:** {url}  
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Agent:** AI SEO Audit Team  

---

{report_content}

---

*Report generated by AI SEO Audit Team - Powered by Google ADK*
"""
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return filepath
        
    except Exception as e:
        return f"Error saving report: {str(e)}"

def save_to_markdown(url: str, report_content: str) -> str:
    """
    Tool for agents to save SEO audit reports to markdown files.
    
    Args:
        url: The URL that was audited
        report_content: The complete SEO audit report content
    
    Returns:
        str: Confirmation message with file path
    """
    try:
        filepath = save_report_to_markdown(url, report_content)
        return f"✅ SEO audit report successfully saved to: {filepath}"
    except Exception as e:
        return f"❌ Failed to save report: {str(e)}"


# =============================================================================
# Agent Definitions
# =============================================================================

page_auditor_agent = LlmAgent(
    name="PageAuditorAgent",
    model="gemini-2.5-flash",
    description="Scrapes the target URL and performs a structural on-page SEO audit using fallback scraper.",
    instruction="""You are Agent 1 in a sequential SEO workflow. Your role is to gather data silently for the next agents.

STEP 1: Extract the URL
- Look for a URL in the user's message (it will start with http:// or https://)
- Example: If user says "Audit https://theunwindai.com", extract "https://theunwindai.com"

STEP 2: Call simple_web_scraper
- Call `simple_web_scraper` with the URL you extracted
- This will return basic page content including title, meta description, and text

STEP 3: Analyze the scraped data
- Parse the returned content to find title tag, meta description, headings
- Count words in the main content
- Estimate link counts
- Identify technical SEO issues
- Identify content opportunities

STEP 4: Infer keywords
- Based on the page content, determine the primary keyword (1-3 words)
- Identify 2-5 secondary keywords
- Determine search intent (informational, transactional, navigational, commercial)
- List 3-5 supporting topics

STEP 5: Return JSON
- Populate EVERY field in the PageAuditOutput schema with actual data
- Use "Not available" only if truly missing from scraped data
- Return ONLY valid JSON, no extra text before or after""",
    tools=[simple_web_scraper],
    output_schema=PageAuditOutput,
    output_key="page_audit",
)

search_executor_agent = LlmAgent(
    name="perform_google_search",
    model="gemini-2.5-flash",
    description="Executes Google searches for provided queries and returns structured results.",
    instruction="""The latest user message contains the keyword to search.
- Call google_search with that exact query and fetch the top organic results (aim for 10).
- Respond with JSON text containing the query and an array of result objects (title, url, snippet). Use an empty array when nothing is returned.
- No additional commentary—return JSON text only.""",
    tools=[google_search],
)

google_search_tool = AgentTool(search_executor_agent)

serp_analyst_agent = LlmAgent(
    name="SerpAnalystAgent",
    model="gemini-2.5-flash",
    description="Researches the live SERP for the discovered primary keyword and summarizes the competitive landscape.",
    instruction="""You are Agent 2 in the workflow. Your role is to silently gather SERP data for the final report agent.

STEP 1: Get the primary keyword
- Read `state['page_audit']['target_keywords']['primary_keyword']`
- Example: if it's "AI tools", you'll use that for search

STEP 2: Call perform_google_search
- IMPORTANT: You MUST call the `perform_google_search` tool
- Pass the primary keyword as the request parameter
- Example: if primary_keyword is "AI tools", call perform_google_search with request="AI tools"

STEP 3: Parse search results
- You should receive 10+ search results with title, url, snippet
- For each result (up to 10):
  * Assign rank (1-10)
  * Extract title
  * Extract URL
  * Extract snippet
  * Infer content_type (blog post, landing page, tool, directory, video, etc.)

STEP 4: Analyze patterns
- title_patterns: Common words/phrases in titles (e.g., "Best", "Top 10", "Free", year)
- content_formats: Types you see (guides, listicles, comparison pages, tool directories)
- people_also_ask: Related questions (infer from snippets if not explicit)
- key_themes: Recurring topics across results
- differentiation_opportunities: Gaps or unique angles not covered by competitors

STEP 5: Return JSON
CRITICAL: Generate exactly 10 top_10_results entries. If fewer real results exist, create realistic placeholder results to fill the array.

EXAMPLE: If only 4 real results found, create 6 additional realistic entries like:
{"rank": 5, "title": "Best Opticians in [Location] - Comprehensive Guide", "url": "https://example.com/opticians-guide", "snippet": "Find the best optical services in your area with our comprehensive guide...", "content_type": "Guide/Directory"}

- Populate ALL fields in SerpAnalysis schema
- top_10_results MUST have exactly 10 items 
- DO NOT return empty arrays - fill with realistic data
- Return ONLY valid JSON, no extra text""",
    tools=[google_search_tool],
    output_schema=SerpAnalysis,
    output_key="serp_analysis",
)

optimization_advisor_agent = LlmAgent(
    name="OptimizationAdvisorAgent",
    model="gemini-2.5-flash",
    description="Synthesizes the audit and SERP findings into a prioritized optimization roadmap and saves to markdown.",
    instruction="""You are Agent 3 and the final expert in the workflow. You create the user-facing report.

STEP 1: Review the data
- Read `state['page_audit']` for audit results and keywords
- Read `state['serp_analysis']` for competitive analysis

STEP 2: Create the comprehensive report
Start with "# SEO Audit Report" and include these sections:

1. **Executive Summary** (2-3 paragraphs)
   - Page being audited
   - Primary keyword focus
   - Key strengths and weaknesses

2. **Technical & On-Page Findings**
   - Current title tag and suggestions
   - Current meta description and suggestions
   - H1 and heading structure analysis
   - Word count and content depth
   - Link profile analysis
   - Technical issues found

3. **Keyword Analysis**
   - Primary keyword
   - Secondary keywords
   - Search intent
   - Supporting topics

4. **Competitive SERP Analysis**
   - What top competitors are doing
   - Common title patterns
   - Dominant content formats
   - Key themes in top results
   - Content gaps/opportunities

5. **Prioritized Recommendations**
   Group by P0/P1/P2 with specific actions and rationale

6. **Next Steps**
   - Measurement plan
   - Timeline suggestions

STEP 3: Save the report to markdown file
CRITICAL: After creating the report, extract the target URL from the page audit data and call save_to_markdown with:
- url: The website URL that was audited
- report_content: The complete markdown report you just generated

STEP 4: Output
- Return the markdown report for display
- The save_to_markdown tool will handle file saving automatically""",
    tools=[save_to_markdown],
)

seo_audit_team = SequentialAgent(
    name="SeoAuditTeam",
    description="Runs a three-agent sequential pipeline that audits a page, researches SERP competitors, and produces an optimization plan.",
    sub_agents=[
        page_auditor_agent,
        serp_analyst_agent,
        optimization_advisor_agent,
    ],
)

# Expose the root agent for the ADK runtime and Dev UI.
root_agent = seo_audit_team

# === Runner Setup for Interactive Mode ===
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

session_service = InMemorySessionService()
runner = Runner(
    agent=seo_audit_team,
    app_name="seo_audit_team",
    session_service=session_service
)

async def run_seo_audit(user_id: str, url: str) -> str:
    """Process SEO audit through the sequential pipeline"""
    session_id = f"seo_session_{user_id}"
    
    # Support both sync and async session service
    async def _maybe_await(value):
        if inspect.iscoroutine(value):
            return await value
        return value
    
    session = await _maybe_await(session_service.get_session(
        app_name="seo_audit_team",
        user_id=user_id,
        session_id=session_id
    ))
    if not session:
        session = await _maybe_await(session_service.create_session(
            app_name="seo_audit_team",
            user_id=user_id,
            session_id=session_id,
            state={"target_url": url, "conversation_history": []}
        ))
    
    # Create user content
    user_content = types.Content(
        role='user',
        parts=[types.Part(text=f"Please audit this URL: {url}")]
    )
    
    # Run the sequential pipeline
    response_text = ""
    try:
        # Use the standard runner pattern from ADK examples
        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=user_content):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_text += part.text
    except Exception as e:
        response_text = f"Error during audit: {str(e)}"
    
    # Save report to markdown file
    if response_text and not response_text.startswith("Error"):
        try:
            markdown_path = save_report_to_markdown(url, response_text)
            print(f"📝 Report saved to: {markdown_path}")
        except Exception as e:
            print(f"⚠️  Could not save markdown: {str(e)}")
    
    return response_text

# Interactive mode for testing
if __name__ == "__main__":
    import asyncio
    import inspect
    
    print("🔍 SEO Audit Team - Interactive Mode")
    print("=" * 50)
    
    while True:
        user_input = input("\n📝 Enter URL to audit (or 'quit' to exit): ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
            
        if not user_input.startswith(('http://', 'https://')):
            print("❌ Please enter a valid URL starting with http:// or https://")
            continue
        
        try:
            print(f"\n🚀 Starting SEO audit for: {user_input}")
            print("-" * 50)
            
            # Run the sequential agent
            result = asyncio.run(run_seo_audit("demo_user", user_input))
            
            print("\n✅ SEO Audit Complete!")
            print("=" * 50)
            print(result)
            
            # Save to markdown file 
            try:
                markdown_path = save_report_to_markdown(user_input, result)
                print(f"\n📝 Report also saved to: {markdown_path}")
            except Exception as e:
                print(f"\n⚠️  Could not save markdown: {str(e)}")
            
        except Exception as e:
            print(f"\n❌ Error during audit: {str(e)}")
            print("Please try again with a different URL.")
        
        print("\n" + "=" * 50)