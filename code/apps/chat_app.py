import os
import json
# pyrefly: ignore [missing-import]
import gradio as gr
import argparse
from pathlib import Path

# Fix path to import our modules
import sys
ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

from chat_agent import process_chat_message

def chatbot_response(message, history, provider):
    """
    Gradio ChatInterface expected signature:
    message: string, current user message
    history: list of [user_msg, bot_msg] tuples
    """
    if not message.strip():
        return "Por favor, escribe una consulta válida."
        
    try:
        # Call our agent
        prov = "openai" if provider == "OpenAI" else ("gemini" if provider == "Gemini" else ("rules" if provider == "Rules/WARM" else "local"))
        result = process_chat_message(message, provider=prov)
        
        # We also want to return the debug info to update the text boxes
        json_str = json.dumps(result.get("extracted_json", {}), indent=2, ensure_ascii=False)
        api_str = json.dumps(result.get("api_results", []), indent=2, ensure_ascii=False)
        
        return result.get("response_text", "No response"), json_str, api_str
        
    except Exception as e:
        return f"Ocurrió un error: {str(e)}", "{}", "[]"

with gr.Blocks(title="CRMs Data Space - Chat Prototype") as demo:
    gr.Markdown("# CRMs Data Space - Chat Agent (Tarea 1)")
    gr.Markdown("Este es un prototipo interactivo para validar la extracción de filtros mediante LLMs y la consulta a una Fake API.")
    
    with gr.Row():
        provider_dropdown = gr.Dropdown(choices=["Rules/WARM", "Local", "OpenAI", "Gemini"], value="Rules/WARM", label="Proveedor LLM")
        
    with gr.Row():
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(label="Chat Principal", height=500)
            msg = gr.Textbox(label="Consulta (ej. 'Dime escombreras de cobre en Andalucía')", placeholder="Escribe aquí...")
            submit = gr.Button("Enviar")
            clear = gr.ClearButton([msg, chatbot])
            
        with gr.Column(scale=1):
            gr.Markdown("### Debug Panel")
            debug_json = gr.Code(language="json", label="JSON de Filtros Extraídos")
            debug_api = gr.Code(language="json", label="Resultados Mock API")

    # Wire everything up
    def user_action(user_message, chat_history, provider_name):
        if chat_history is None:
            chat_history = []
        chat_history.append({"role": "user", "content": str(user_message)})
        return "", chat_history

    def bot_action(chat_history, provider_name):
        last_msg = chat_history[-1]
        
        if isinstance(last_msg, dict):
            user_message = last_msg.get("content", "")
        elif hasattr(last_msg, "content"):
            user_message = last_msg.content
        elif isinstance(last_msg, (list, tuple)):
            user_message = last_msg[0]
        else:
            user_message = str(last_msg)
            
        if isinstance(user_message, (list, tuple)):
            user_message = user_message[0] if len(user_message) > 0 else ""
            
        user_message_str = str(user_message)
        
        bot_response, out_json, out_api = chatbot_response(user_message_str, chat_history[:-1], provider_name)
        chat_history.append({"role": "assistant", "content": str(bot_response)})
        return chat_history, out_json, out_api

    msg.submit(user_action, [msg, chatbot, provider_dropdown], [msg, chatbot], queue=False).then(
        bot_action, [chatbot, provider_dropdown], [chatbot, debug_json, debug_api]
    )
    submit.click(user_action, [msg, chatbot, provider_dropdown], [msg, chatbot], queue=False).then(
        bot_action, [chatbot, provider_dropdown], [chatbot, debug_json, debug_api]
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-cpu', action='store_true', help='Force CPU execution')
    parser.add_argument('-gpu', action='store_true', help='Enable GPU execution')
    args = parser.parse_args()
    
    if args.gpu:
        os.environ["USE_GPU"] = "1"
    else:
        os.environ["USE_GPU"] = "0"
        
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
