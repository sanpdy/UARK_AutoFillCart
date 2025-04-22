from recipdf_app.agent_definitions.agent_utilities import get_client_wrapper_for_llm_api_provider


# Agent Superclass Definition
class Agent:
    def __init__(self, llm='gpt-4o-mini', llm_api_provider='openai', embedding_model='text-embedding-3-small',
                 embedding_api_provider='openai', system_prompt=None, skill_library_db=None):
        # Declare attributes for generating LLM responses
        # self.openai_api_wrapper = get_client_wrapper_for_llm_api_provider('openai')
        # self.anthropic_api_wrapper = get_client_wrapper_for_llm_api_provider('anthropic')
        self.llm_api_provider = llm_api_provider
        self.llm_api_wrapper = get_client_wrapper_for_llm_api_provider(llm_api_provider)
        self.model = llm

        # Declare attributes for generating embeddings
        self.embedding_api_provider = embedding_api_provider
        self.embedding_api_wrapper = get_client_wrapper_for_llm_api_provider(embedding_api_provider)
        self.embedding_model = embedding_model

        # Declare attributes for storing the agent's message context and optional system message
        self.system_prompt = system_prompt
        self.system_message = None
        self.context = None
        self.reset_context()

        # Store the skill library instantiated in __main__.py as an attribute of the Agent superclass
        if skill_library_db is not None:
            # NOTE: Using a shared instance of the SkillLibraryDatabase class for now
            #  Disadvantages:
            #   -Not Future-Proof for Thread Safety
            #  Advantages:
            #   -Resource Usage
            self.skill_library_db = skill_library_db

    def reset_context(self):
        # Default behavior for resetting `context` attribute
        if self.system_prompt:
            self.system_message = {
                'role': 'system',
                'content': self.system_prompt
            }
            self.context = [self.system_message]
        else:
            self.context = []
