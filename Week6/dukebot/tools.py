# tools.py
from urllib.parse import quote
from langchain.tools import Tool
import requests
import json
import os
from rapidfuzz import fuzz
from langchain_aws.chat_models import BedrockChat
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
import logging
import traceback

class EventFilters(BaseModel):
    """A class to represent the filters for events."""
    groups: list[str] = Field(description="The groups to filter events by.")
    categories: list[str] = Field(description="The categories to filter events by.")

# Define the tools
def load_options_from_file(filename):
    """
    Load valid options from a text file, where each line is an option.
    Args:
        filename (str): Path to the text file containing valid options.
    Returns:
        list: List of valid options.
    """
    with open(filename, 'r') as file:
        return [line.strip() for line in file]
    
# Try to load the valid options
try:
    valid_groups = load_options_from_file('resources/groups.txt')
    valid_categories = load_options_from_file('resources/categories.txt')
    valid_subjects = load_options_from_file('resources/subjects.txt')
except FileNotFoundError as e:
    print(f"Warning: Could not load options file: {e}")
    valid_groups = []
    valid_categories = []
    valid_subjects = []

def filter_candidates(query: str, candidates: list, top_n: int = 10) -> list:
    """
    Use fuzzy string matching to choose the top_n candidate strings from candidates
    that best match the query.
    """
    # Compute a similarity score for each candidate
    scored = [(candidate, fuzz.token_set_ratio(query, candidate)) for candidate in candidates]
    # Sort candidates by score descending
    scored.sort(key=lambda x: x[1], reverse=True)
    # Return the top_n candidates; if no candidates are good matches, return an empty list.
    return [candidate for candidate, score in scored[:top_n]]

def load_valid_values(filename: str) -> list:
    """
    Load valid values from a text file, removing empty lines and stripping whitespace.
    Args:
        filename (str): Path to the text file containing valid values.
    Returns:
        list: List of valid values.
    """
    with open(filename, "r", encoding="utf8") as f:
        # Remove empty lines and strip whitespace
        return [line.strip() for line in f if line.strip()]

def load_valid_groups():
    """
    Load valid groups from the groups.txt file.
    """
    return load_valid_values("resources/groups.txt")

def load_valid_categories():
    """
    Load valid categories from the categories.txt file.
    """
    return load_valid_values("resources/categories.txt")

def llm_map_prompt_to_filters(prompt: str):
    """
    Uses an LLM to map a natural language prompt to valid groups and categories.
    The LLM receives reduced candidate lists (using fuzzy matching) from the full .txt files 
    and is instructed to return a JSON object with the chosen groups and categories.
    
    Expected JSON output format:
       {"groups": ["Group1", "Group2"], "categories": ["Category1", "Category2"]}
    
    If the LLM fails to return valid JSON, it defaults to returning empty lists.
    This function is designed to be used as a tool in a LangChain agent.

    Args:
        prompt (str): Natural language prompt describing the query for events.
    Returns:
        tuple: A tuple containing two lists:
            - groups (list): List of selected groups.
            - categories (list): List of selected categories.
    """
    # Load full lists from files
    valid_groups = load_valid_groups()
    valid_categories = load_valid_categories()

    # Pre-filter the lists using fuzzy matching to reduce tokens
    filtered_groups = filter_candidates(prompt, valid_groups, top_n=10)
    filtered_categories = filter_candidates(prompt, valid_categories, top_n=10)
    
    print("Filtered groups:", filtered_groups)
    print("Filtered categories:", filtered_categories)
    # If filtering returns an empty list, default to ["All"]
    if not filtered_groups:
        filtered_groups = ["All"]
    if not filtered_categories:
        filtered_categories = ["All"]

    # Initialize the Bedrock LLM
    llm = BedrockChat(
        model_id="anthropic.claude-3-sonnet-20240229-v1:0",
        model_kwargs={"temperature": 0.0},
    ).with_structured_output(EventFilters)

    # Compose the prompt
    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", "You are an expert at mapping natural language input to valid filter values. "
                       "I will provide you with a list of valid groups and valid categories, along with a user query. "
                       "Your task is to select from these lists only the values that best match the query. "
                       "If none of the items in a list match, then based on the query, return ['All'] if the query implies "
                       "retrieving all events, or an empty list if it does not. "
                       "Return only a valid JSON object with two keys: 'groups' and 'categories'."),
            ("human", "Valid groups: {groups}\n"
                      "Valid categories: {categories}\n"
                      "User query: \"{query}\"\n\n"
                      "Based on the lists above, select the groups and categories that best match the user query. "
                      "Return your answer strictly as a JSON object with two keys: 'groups' and 'categories'.")
        ]
    )

    chain = prompt_template | llm

    try:
        # Invoke the LLM chain
        response = chain.invoke({
            "groups": json.dumps(filtered_groups),
            "categories": json.dumps(filtered_categories),
            "query": prompt
        })
        
        groups = response.groups
        categories = response.categories
    except Exception as e:
        print(f"LLM mapping failed: {str(e)}")
        groups = []
        categories = []

    return groups, categories

def events_from_duke_api(feed_type: str = "json",
                             future_days: int = 45,
                             groups: list = ['All'],
                             categories: list = ['All'],
                             filter_method_group: bool = True,
                             filter_method_category: bool = True) -> str:
    """
    Fetch events from Duke University's public calendar API with optional filters.

    Parameters:
        feed_type (str): Format of the returned data. Acceptable values include:
                         'rss', 'js', 'ics', 'csv', 'json', 'jsonp'. Defaults to 'json'.
        future_days (int): Number of days into the future for which to fetch events.
                           Defaults to 45.
        groups (list):  The organizer or host groups of the events or the related groups in events. For example,
                        '+DataScience (+DS)' refers to events hosted by the DataScience program.
                        Use 'All' to include events from all groups. 
        categories (list): 
                        The thematic or topical category of the events. For example,
                        'Academic Calendar Dates', 'Alumni/Reunion', or 'Artificial Intelligence'.
                         Use 'All' to include events from all categories.
        filter_method_group (bool): 
            - False: Event must match ALL specified groups (AND).
            - True: Event may match ANY of the specified groups (OR).
        filter_method_category (bool): 
            - False: Event must match ALL specified categories (AND).
            - True: Event may match ANY of the specified categories (OR).

    Returns:
        str: Raw calendar data (e.g., in JSON, XML, or ICS format) or an error message.
    """
    
    # When feed_type is not one of these types, add the simple feed_type parameter.
    feed_type_param = ""
    if feed_type not in ['rss', 'js', 'ics', 'csv']:
        feed_type_param = "feed_type=simple"
    
    # If feed_type is not one of these types, add the simple feed_type parameter.
    feed_type_url = feed_type_param if feed_type_param else ""

    # If the filter_method_group is True, then the group_url is empty.
    if filter_method_group:
        if 'All' in groups:
            group_url = ""
        else:
            group_url = ""
            for group in groups:
                group_url+='&gfu[]='+quote(group, safe="")
    else:
        if 'All' in groups:
            group_url = ""
        else:
            group_url = "&gf[]=" + quote(groups[0], safe="")
            for group in groups[1:]:
                group_url += "&gf[]=" + quote(group, safe="")

    if filter_method_category:
        if 'All' in categories:
            category_url = ""
        else:
            category_url = ""
            for category in categories:
                category_url += '&cfu[]=' + quote(category, safe="")
    else:
        if 'All' in categories:
            category_url = ""
        else:
            category_url = ""
            for category in categories:
                category_url += "&cf[]=" + quote(category, safe="")

    url = f'https://calendar.duke.edu/events/index.{feed_type}?{category_url}{group_url}&future_days={future_days}&{feed_type_url}'

    logger = logging.getLogger("DukeAPI")
    logger.info(f"Requesting events: feed_type={feed_type}, future_days={future_days}, groups={groups}, categories={categories}, URL: {url}")
    try:
        response = requests.get(url)
        logger.info(f"Response status: {response.status_code}, Body: {response.text[:500]}")
        if response.status_code == 200:
            return response.text[:1000]
        else:
            logger.error(f"Failed to fetch data: {response.status_code} | Response: {response.text}")
            return f"Failed to fetch data: {response.status_code}\nResponse: {response.text}"
    except Exception as e:
        logger.error(f"Exception occurred: {str(e)}\nTraceback: {traceback.format_exc()}")
        return f"Exception occurred: {str(e)}\nTraceback: {traceback.format_exc()}"
    
def get_events_from_duke_api(prompt: str,
                                   feed_type: str = "json",
                                   future_days: int = 45,
                                   filter_method_group: bool = True,
                                   filter_method_category: bool = True) -> str:
    """
    Retrieve events from Duke University's public calendar API based on a natural language prompt.

    Args:
        prompt (str): Natural language prompt describing the query for events.

        feed_type (str): Format of the returned data. Acceptable values include:
                            'rss', 'js', 'ics', 'csv', 'json', 'jsonp'. Defaults to 'json'.

        future_days (int): Number of days into the future for which to fetch events.
                            Defaults to 45.

        filter_method_group (bool): 
        - False: Event must match ALL specified groups (AND).
        - True: Event may match ANY of the specified groups (OR).

        filter_method_category (bool): 
        - False: Event must match ALL specified categories (AND).
        - True: Event may match ANY of the specified categories (OR).
    Returns:
        str: Raw calendar data (e.g., in JSON, XML, or ICS format) or an error message.
    """
    # Use the LLM-based mapping to get groups and categories
    groups, categories = llm_map_prompt_to_filters(prompt)
    if not groups and not categories:
        return "Error: Unable to find any related groups or categories for the given prompt."
    
    print(f"LLM mapped prompt '{prompt}' to groups {groups} and categories {categories}")
    
    # Call the original Duke API tool with the determined filters
    result = events_from_duke_api(
        feed_type=feed_type,
        future_days=future_days,
        groups=groups,
        categories=categories,
        filter_method_group=filter_method_group,
        filter_method_category=filter_method_category
    )
    print(f"Events API result: {result[:500]}")
    return result

def get_events_from_duke_api_single_input(arg_str: str) -> str:
    """
    A wrapper that parses a single comma-separated string input and calls
    get_events_from_duke_api with the appropriate arguments.

    Expected input format:
        "prompt, feed_type, future_days, filter_method_group, filter_method_category"

    - prompt (str): Required natural language query for event retrieval.
    - feed_type (str): Optional; defaults to 'json' if not provided.
    - future_days (int): Optional; defaults to 45 if not provided.
    - filter_method_group (bool): Optional; defaults to True if not provided.
    - filter_method_category (bool): Optional; defaults to True if not provided.

    If only the prompt is provided, the default values are used for the remaining parameters.
    Returns:
        str: Raw calendar data (e.g., in JSON, XML, or ICS format) or an error message.
    """
    # Split the input string by commas and strip whitespace from each part.
    parts = [part.strip() for part in arg_str.split(",")]
    
    # Required parameter: prompt.
    if len(parts) < 1 or not parts[0]:
        return "Error: The prompt must be provided."
    prompt = parts[0]
    
    # Optional parameter: feed_type. Defaults to "json".
    feed_type = parts[1] if len(parts) > 1 and parts[1] else "json"
    
    # Optional parameter: future_days. Defaults to 45.
    try:
        future_days = int(parts[2]) if len(parts) > 2 and parts[2] else 45
    except ValueError:
        future_days = 45  # fallback if parsing fails
    
    # Optional parameter: filter_method_group. Defaults to True.
    # If provided and equals "False" (case-insensitive), then use False.
    filter_method_group = True
    if len(parts) > 3:
        if parts[3].lower() in ["false", "0"]:
            filter_method_group = False

    # Optional parameter: filter_method_category. Defaults to True.
    filter_method_category = True
    if len(parts) > 4:
        if parts[4].lower() in ["false", "0"]:
            filter_method_category = False

    # Call the original function with the parsed parameters.
    return get_events_from_duke_api(
        prompt=prompt,
        feed_type=feed_type,
        future_days=future_days,
        filter_method_group=filter_method_group,
        filter_method_category=filter_method_category
    )

def format_curriculum_summary(data):
    """
    Format curriculum data (dict or list) into a user-friendly summary string.
    Always returns a string, never raises.
    Strictly enforce type checks and fallback error messages.
    """
    if not isinstance(data, (dict, list)):
        return "Error: Curriculum data is not a valid JSON object or list."
    try:
        if isinstance(data, dict):
            resp = data.get('ssr_get_courses_resp', {})
            if not isinstance(resp, dict):
                return "Error: Unexpected curriculum response structure (missing 'ssr_get_courses_resp')."
            result = resp.get('course_search_result', {})
            if not isinstance(result, dict):
                return "Error: Unexpected curriculum response structure (missing 'course_search_result')."
            subjects = result.get('subjects', {})
            subject = None
            if isinstance(subjects, dict):
                subject = subjects.get('subject', {})
            elif isinstance(subjects, list):
                subject = subjects[0] if subjects else {}
            else:
                subject = subjects
            if isinstance(subject, list):
                subject = subject[0] if subject else {}
            if not isinstance(subject, dict):
                return "Error: Unexpected curriculum response structure (subject missing or not a dict)."
            course_summaries = subject.get('course_summaries', {}).get('course_summary', [])
            if isinstance(course_summaries, dict):
                course_summaries = [course_summaries]
            if not isinstance(course_summaries, list):
                return "Error: Unexpected curriculum response structure (course_summaries not a list)."
            if not course_summaries:
                return "No courses found for this subject."
            lines = [f"**{subject.get('subject', '')} - {subject.get('subject_lov_descr', '')}** ({len(course_summaries)} courses):"]
            for course in course_summaries[:5]:
                code = course.get('crse_id', '')
                offer = course.get('crse_offer_nbr', '')
                title = course.get('title_long', course.get('title', ''))
                desc = course.get('descrlong', course.get('descr', ''))
                lines.append(f"- **{code}** (Offer {offer}): {title}\n    {desc}")
            if len(course_summaries) > 5:
                lines.append(f"...and {len(course_summaries)-5} more. Refine your query for more details.")
            return "\n".join(lines)
        elif isinstance(data, list):
            if not data:
                return "No curriculum data found."
            lines = ["**Courses:**"]
            for course in data[:5]:
                code = course.get('crse_id', '')
                offer = course.get('crse_offer_nbr', '')
                title = course.get('title_long', course.get('title', ''))
                desc = course.get('descrlong', course.get('descr', ''))
                lines.append(f"- **{code}** (Offer {offer}): {title}\n    {desc}")
            if len(data) > 5:
                lines.append(f"...and {len(data)-5} more. Refine your query for more details.")
            return "\n".join(lines)
        else:
            return "No curriculum data found."
    except Exception as e:
        return f"Error: Could not process curriculum data. (Error: {str(e)})"

def get_curriculum_with_subject_from_duke_api(subject: str):
    """
    Retrieve curriculum information from Duke University's API by specifying a subject code.
    Returns information about available courses.
    Strictly enforce: (1) parse as JSON, (2) handle parse errors, (3) handle structure errors, (4) never raise.
    Args:
        subject (str): The subject code to get curriculum data for. For example, the subject code is 'AIPI' for Artificial Intelligence for Product Innovation.
    Returns:
        str: User-friendly curriculum summary or an error message.
    """
    logger = logging.getLogger("DukeAPI")
    subject_url = quote(subject, safe="")
    url = f'https://streamer.oit.duke.edu/curriculum/courses/subject/{subject_url}?access_token=19d3636f71c152dd13840724a8a48074'
    logger.info(f"Requesting curriculum for subject: {subject}, URL: {url}")
    try:
        response = requests.get(url)
        logger.info(f"Response status: {response.status_code}, Body: {response.text[:500]}")
        if response.status_code == 200:
            try:
                data = json.loads(response.text)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {str(e)} | Raw response: {response.text}")
                return f"Error: Could not parse API response. Exception: {str(e)}\nRaw response: {response.text}"
            return format_curriculum_summary(data)
        else:
            logger.error(f"Failed to fetch data: {response.status_code} | Response: {response.text}")
            return f"Failed to fetch data: {response.status_code}\nResponse: {response.text}"
    except Exception as e:
        logger.error(f"Exception occurred: {str(e)}\nTraceback: {traceback.format_exc()}")
        return f"Exception occurred: {str(e)}\nTraceback: {traceback.format_exc()}"
    
def get_detailed_course_information_from_duke_api(course_id: str, course_offer_number: str):
    """
    Retrieve curriculum information from Duke University's API by specifying a course ID and course offer number, allowing you to access detailed information about a specific course.
    Parameters:
        course_id (str): The course ID to get curriculum data for. For example, the course ID is 029248' for General African American Studies.
        course_offer_number (str): The course offer number to get curriculum data for. For example, the course offer number is '1' for General African American Studies.
    Returns:
        str: Raw curriculum data in JSON format or an error message.
    """
    logger = logging.getLogger("DukeAPI")
    url = f'https://streamer.oit.duke.edu/curriculum/courses/crse_id/{course_id}/crse_offer_nbr/{course_offer_number}?access_token=19d3636f71c152dd13840724a8a48074'
    logger.info(f"Requesting detailed course info: course_id={course_id}, offer_number={course_offer_number}, URL: {url}")
    try:
        response = requests.get(url)
        logger.info(f"Response status: {response.status_code}, Body: {response.text[:500]}")
        if response.status_code == 200:
            return response.text
        else:
            logger.error(f"Failed to fetch data: {response.status_code} | Response: {response.text}")
            return f"Failed to fetch data: {response.status_code}\nResponse: {response.text}"
    except Exception as e:
        logger.error(f"Exception occurred: {str(e)}\nTraceback: {traceback.format_exc()}")
        return f"Exception occurred: {str(e)}\nTraceback: {traceback.format_exc()}"

def get_course_details_single_input(arg_str: str) -> str:
    # Expect a single string in the format "course_id,course_offer_number", e.g. "027568,1"
    try:
        course_id, course_offer_number = arg_str.split(",")
        course_id = course_id.strip()
        course_offer_number = course_offer_number.strip()
        return get_detailed_course_information_from_duke_api(course_id, course_offer_number)
    except ValueError:
        return "Error: Please provide input in the form 'course_id,course_offer_number'"
    
def get_people_information_from_duke_api(name: str):
    """
    Retrieve people information from Duke University's API by specifying a name, allowing you to access detailed information about a specific person.

    Parameters:
        name (str): The name to get people data for. For example, the name is 'John Doe'.

    Returns:
        str: Raw people data in JSON format or an error message.
    """
    logger = logging.getLogger("DukeAPI")
    name_url = quote(name, safe="")
    url = f'https://streamer.oit.duke.edu/ldap/people?q={name_url}&access_token=19d3636f71c152dd13840724a8a48074'
    logger.info(f"Requesting people info for name: {name}, URL: {url}")
    try:
        response = requests.get(url)
        logger.info(f"Response status: {response.status_code}, Body: {response.text[:500]}")
        if response.status_code == 200:
            return response.text
        else:
            logger.error(f"Failed to fetch data: {response.status_code} | Response: {response.text}")
            return f"Failed to fetch data: {response.status_code}\nResponse: {response.text}"
    except Exception as e:
        logger.error(f"Exception occurred: {str(e)}\nTraceback: {traceback.format_exc()}")
        return f"Exception occurred: {str(e)}\nTraceback: {traceback.format_exc()}"

def search_subject_by_code(query):
    """
    Search for subjects matching a code or description.
    
    Parameters:
        query (str): The search term to look for in subject codes or descriptions.
        
    Returns:
        str: JSON string containing matching subjects.
    """
    # Search by code (like "AIPI" or "CS")
    code_matches = []
    for subject in valid_subjects:
        parts = subject.split(' - ')
        if len(parts) >= 2:
            code = parts[0].strip()
            # Look for the query in the code part
            if query.lower() in code.lower() or query.lower().replace(' ', '') in code.lower().replace('-', '').replace(' ', ''):
                code_matches.append(subject)
    
    # Search by name/description (like "computer science" or "artificial intelligence")
    name_matches = []
    for subject in valid_subjects:
        parts = subject.split(' - ')
        if len(parts) >= 2:
            name = parts[1].strip()
            # Look for the query in the name part
            if query.lower() in name.lower():
                name_matches.append(subject)
    
    # Combine results with code matches first (removing duplicates)
    all_matches = code_matches + [m for m in name_matches if m not in code_matches]
    
    return json.dumps({
        "query": query,
        "matches": all_matches[:5]  # Limit to top 5 matches
    })

def search_group_format(query):
    """
    Search for groups matching a query string.
    
    Parameters:
        query (str): The search term to look for in group names.
        
    Returns:
        str: JSON string containing matching groups.
    """
    matches = [g for g in valid_groups if query.lower() in g.lower()]
    
    return json.dumps({
        "query": query,
        "matches": matches[:5]  # Limit to top 5 matches
    })

def search_category_format(query):
    """
    Search for categories matching a query string.
    
    Parameters:
        query (str): The search term to look for in category names.
        
    Returns:
        str: JSON string containing matching categories.
    """
    matches = [c for c in valid_categories if query.lower() in c.lower()]
    
    return json.dumps({
        "query": query,
        "matches": matches[:5]  # Limit to top 5 matches
    })

def get_pratt_info_from_serpapi(query="Duke Pratt School of Engineering", api_key=None, filter_domain=True):
     """
     Retrieve information about Duke's Pratt School of Engineering using SerpAPI.
     Args:
        query (str): The search query to use for retrieving information.
        api_key (str): Optional; SerpAPI key. If not provided, it will be read from the environment variable SERPAPI_API_KEY.
        filter_domain (bool): If True, filter results to prioritize pratt.duke.edu and duke.edu domains.
     Returns:
        str: JSON string containing the search results or an error message.
     """
     if api_key is None:
         api_key = os.environ.get("SERPAPI_API_KEY")
         if not api_key:
             return json.dumps({"error": "SerpAPI key not found. Please provide an API key or set SERPAPI_API_KEY environment variable."})
     
     # Ensure the query includes Duke Pratt
     if "duke pratt" not in query.lower():
         query = f"Duke Pratt School of Engineering {query}"
     
     # Construct the SerpAPI URL with the query
     encoded_query = quote(query)
     url = f"https://serpapi.com/search.json?q={encoded_query}&engine=google&num=10&api_key={api_key}"
     
     try:
         # Make the request to SerpAPI
         response = requests.get(url, timeout=15)
         if response.status_code == 200:
             search_results = response.json()
             return process_serpapi_results(search_results, filter_domain)
         else:
             return f"Error: SerpAPI returned status {response.status_code}"
     except Exception as e:
         return f"Error occurred while searching SerpAPI: {str(e)}"
 
def process_serpapi_results(search_results, filter_domain=True):
     """
     Process and filter SerpAPI results to extract the most relevant information.
     Args:
        search_results (dict): The raw search results from SerpAPI.
        filter_domain (bool): If True, filter results to prioritize pratt.duke.edu and duke.edu domains.
     Returns:
        dict: Processed search results containing metadata, organic results, knowledge graph, and related questions.
     """
     processed_data = {
         "search_metadata": {},
         "organic_results": [],
         "knowledge_graph": {},
         "related_questions": []
     }
     
     # Extract search metadata
     if "search_metadata" in search_results:
         processed_data["search_metadata"] = {
             "query": search_results["search_metadata"].get("query", ""),
             "total_results": search_results.get("search_information", {}).get("total_results", 0)
         }
     
     # Extract organic results
     if "organic_results" in search_results:
         organic_results = search_results["organic_results"]
         
         # Filter for duke.edu domains if requested
         if filter_domain:
             # More aggressive filtering - require "duke" in the link or snippet
             filtered_results = [result for result in organic_results 
                                if "duke" in result.get("link", "").lower() or 
                                   "duke" in result.get("snippet", "").lower()]
             
             # Further prioritize pratt.duke.edu results
             pratt_results = [result for result in filtered_results 
                             if "pratt.duke.edu" in result.get("link", "")]
             
             other_duke_results = [result for result in filtered_results 
                                  if "pratt.duke.edu" not in result.get("link", "")]
             
             # Combine with pratt results first, then other duke results
             processed_results = pratt_results + other_duke_results
             
             # If we have no results after filtering, use the original results
             if not processed_results and organic_results:
                 processed_results = organic_results[:5]  # Just take the top 5
         else:
             processed_results = organic_results
         
         # Extract the most useful information from each result
         for result in processed_results[:8]:  # Limit to top 8 results
             processed_data["organic_results"].append({
                 "title": result.get("title", ""),
                 "link": result.get("link", ""),
                 "snippet": result.get("snippet", ""),
                 "source": result.get("source", "")
             })
     
     # Extract knowledge graph information if available
     if "knowledge_graph" in search_results:
         kg = search_results["knowledge_graph"]
         processed_data["knowledge_graph"] = {
             "title": kg.get("title", ""),
             "type": kg.get("type", ""),
             "description": kg.get("description", ""),
             "website": kg.get("website", ""),
             "address": kg.get("address", "")
         }
     
     # Extract related questions if available
     if "related_questions" in search_results:
         for question in search_results["related_questions"][:4]:  # Limit to top 4 questions
             processed_data["related_questions"].append({
                 "question": question.get("question", ""),
                 "answer": question.get("answer", "")
             })
     
     return processed_data
