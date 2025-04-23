import logging

logger = logging.getLogger(__name__)

def serialize_context(context):
    """
    Convert context to a serializable format
    """
    serializable_context = []
    
    for message in context:
        if isinstance(message, dict):
            serializable_context.append(message)
        elif hasattr(message, 'role') and hasattr(message, 'content'):
            message_dict = {'role': message.role, 'content': message.content}
            
            if hasattr(message, 'tool_calls') and message.tool_calls:
                tool_calls_list = []
                for tool_call in message.tool_calls:
                    tool_call_dict = {}
                    
                    if hasattr(tool_call, 'id'):
                        tool_call_dict['id'] = tool_call.id
                    if hasattr(tool_call, 'type'):
                        tool_call_dict['type'] = tool_call.type
                    if hasattr(tool_call, 'function'):
                        function_dict = {}
                        if hasattr(tool_call.function, 'name'):
                            function_dict['name'] = tool_call.function.name
                        if hasattr(tool_call.function, 'arguments'):
                            function_dict['arguments'] = tool_call.function.arguments
                        tool_call_dict['function'] = function_dict
                    
                    tool_calls_list.append(tool_call_dict)
                
                message_dict['tool_calls'] = tool_calls_list
            
            serializable_context.append(message_dict)
        else:
            logger.warning(f"Unexpected message type in context: {type(message)}")
            serializable_context.append({
                'role': 'system',
                'content': str(message)
            })
    
    return serializable_context