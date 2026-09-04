import os
import json
import gradio as gr
import folium
import unicodedata

from chat_agent import extract_filters, generate_natural_response
from mock_api import query_data_space, MOCK_DATABASE

def create_map(api_results):
    """
    Creates a Folium map based on the filtered results.
    """
    # Centered in Spain
    m = folium.Map(location=[40.4168, -3.7038], zoom_start=6)
    
    for site in api_results:
        lat = site.get("lat")
        lon = site.get("lon")
        if lat is not None and lon is not None:
            popup_html = f"<b>{site['site_name']}</b><br>"
            region_name = str(site.get('region') or '').title()
            popup_html += f"Region: {region_name}<br>"
            popup_html += f"Commodities: {', '.join(site.get('commodities', []))}<br>"
            status = site.get('project_status') or site.get('mine_status') or 'unknown'
            popup_html += f"Status: {str(status).title()}"
            
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(m)
            
    return m._repr_html_()

# Initial map with all sites
initial_map_html = create_map(MOCK_DATABASE)

with gr.Blocks(title="CRMs Data Space Dashboard", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# CRMs Data Space - Interactive Dashboard")
    gr.Markdown("Prototipo de buscador avanzado y chatbot integrado con LLM para filtrar el espacio de datos.")
    
    with gr.Row():
        provider_dropdown = gr.Dropdown(choices=["Rules/WARM", "Local", "OpenAI", "Gemini"], value="Rules/WARM", label="Proveedor LLM")

    with gr.Row():
        # LEFT COLUMN: Filters (Read Only to show LLM extraction)
        with gr.Column(scale=1):
            gr.Markdown("### 🔍 Filtros Detectados")
            gr.Markdown("*El modelo completará estos filtros automáticamente basándose en tu consulta.*")
            AVAILABLE_REGIONS = ["andalucia", "asturias", "castilla y leon", "galicia", "extremadura", "alentejo"]
            AVAILABLE_COMMODITIES = ["coal", "copper", "silver", "gold", "tungsten", "tin", "lithium", "nickel", "cobalt", "zinc", "lead", "tantalum", "niobium"]
            AVAILABLE_STATUSES = ["active", "inactive", "care and maintenance", "development"]
            
            filter_region = gr.CheckboxGroup(choices=AVAILABLE_REGIONS, label="Regiones detectadas", interactive=True)
            filter_commodity = gr.CheckboxGroup(choices=AVAILABLE_COMMODITIES, label="Materiales/Elementos detectados", interactive=True)
            filter_status = gr.CheckboxGroup(choices=AVAILABLE_STATUSES, label="Estado del proyecto", interactive=True)
            filter_json = gr.Code(language="json", label="Filtros Crudos (JSON)", interactive=False)
            
        # CENTER COLUMN: Map
        with gr.Column(scale=3):
            gr.Markdown("### 🗺️ Mapa de Escombreras y Sitios")
            map_view = gr.HTML(value=initial_map_html)
 
        # RIGHT COLUMN: Chat
        with gr.Column(scale=2):
            gr.Markdown("### 💬 Chat Asistente")
            chatbot = gr.Chatbot(label="CRMs Assistant", height=400)
            msg = gr.Textbox(label="Tu Consulta", placeholder="Ej: Dime escombreras de wolframio en Galicia...")
            
            with gr.Row():
                submit = gr.Button("Enviar", variant="primary")
                clear = gr.ClearButton([msg, chatbot])
 
    # The interaction pipeline
    def user_action(user_message, chat_history):
        if chat_history is None:
            chat_history = []
        chat_history.append({"role": "user", "content": str(user_message)})
        return "", chat_history
 
    def extract_and_update_filters(chat_history, provider_name):
        """
        Step 1: Extract filters from the last user message and query the DB.
        """
        last_msg = chat_history[-1]
        
        # Safely extract text string from Gradio
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
        prov = "openai" if provider_name == "OpenAI" else ("gemini" if provider_name == "Gemini" else ("rules" if provider_name == "Rules/WARM" else "local"))
        
        # 1. Extract
        parsed_json = extract_filters(user_message_str, provider=prov)
        raw_filters = parsed_json.get("filters", {})
        
        # Helper to normalize accents and lowercase
        def clean_text(text):
            if not isinstance(text, str): return text
            t = text.lower()
            return ''.join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')
            
        # Dynamically add any extracted regions and commodities to choices if not already present
        current_regions = list(AVAILABLE_REGIONS)
        for r in raw_filters.get("regions", []):
            clean_r = clean_text(r)
            if clean_r and clean_r not in current_regions:
                current_regions.append(clean_r)
                
        current_commodities = list(AVAILABLE_COMMODITIES)
        for c in raw_filters.get("commodities", []):
            clean_c = clean_text(c)
            if clean_c and clean_c not in current_commodities:
                current_commodities.append(clean_c)

        # 2. Sanitize and match against catalog (removes hallucinations like 'elementos' and fixes accents like 'león')
        reg_list = [clean_text(r) for r in raw_filters.get("regions", []) if clean_text(r) in current_regions]
        comm_list = [clean_text(c) for c in raw_filters.get("commodities", []) if clean_text(c) in current_commodities]
        stat_list = [clean_text(s) for s in raw_filters.get("project_status", []) if clean_text(s) in AVAILABLE_STATUSES]
        
        filters_dict = {}
        if reg_list: filters_dict["regions"] = reg_list
        if comm_list: filters_dict["commodities"] = comm_list
        if stat_list: filters_dict["project_status"] = stat_list
        
        # 3. Query with clean filters
        api_results = query_data_space(filters_dict)
        
        # 4. Update UI
        json_str = json.dumps(filters_dict, indent=2, ensure_ascii=False)
        
        map_html = create_map(api_results)
        
        # We also need to pass internal state to the next step
        internal_state = {
            "query": user_message_str,
            "parsed_json": parsed_json,
            "api_results": api_results,
            "provider": prov
        }
        
        return (
            gr.CheckboxGroup(choices=current_regions, value=reg_list),
            gr.CheckboxGroup(choices=current_commodities, value=comm_list),
            gr.CheckboxGroup(value=stat_list),
            json_str,
            map_html,
            internal_state
        )

    def generate_response(chat_history, internal_state):
        """
        Step 2: Generate natural language response
        """
        query = internal_state["query"]
        parsed_json = internal_state["parsed_json"]
        api_results = internal_state["api_results"]
        prov = internal_state["provider"]
        
        bot_response = generate_natural_response(query, parsed_json, api_results, provider=prov)
        
        chat_history.append({"role": "assistant", "content": bot_response})
        return chat_history

    # State component to pass data between events
    state_pipeline = gr.State()

    # When user submits, first add to chat history immediately
    action_1 = msg.submit(
        user_action, 
        [msg, chatbot], 
        [msg, chatbot], 
        queue=False
    )
    # Then extract filters and update UI (map + filter panel)
    action_2 = action_1.then(
        extract_and_update_filters, 
        [chatbot, provider_dropdown], 
        [filter_region, filter_commodity, filter_status, filter_json, map_view, state_pipeline]
    )
    # Finally, generate the response using the results and append to chat
    action_2.then(
        generate_response,
        [chatbot, state_pipeline],
        [chatbot]
    )
    
    # Repeat for submit button click
    action_3 = submit.click(
        user_action, 
        [msg, chatbot], 
        [msg, chatbot], 
        queue=False
    )
    action_4 = action_3.then(
        extract_and_update_filters, 
        [chatbot, provider_dropdown], 
        [filter_region, filter_commodity, filter_status, filter_json, map_view, state_pipeline]
    )
    action_4.then(
        generate_response,
        [chatbot, state_pipeline],
        [chatbot]
    )

    # Allow manual filter interaction to update the map
    def manual_filter_update(regions, commodities, statuses):
        filters_dict = {}
        if regions:
            filters_dict["regions"] = regions
        if commodities:
            filters_dict["commodities"] = commodities
        if statuses:
            filters_dict["project_status"] = statuses
            
        api_results = query_data_space(filters_dict)
        map_html = create_map(api_results)
        json_str = json.dumps(filters_dict, indent=2, ensure_ascii=False)
        return json_str, map_html

    filter_region.change(manual_filter_update, [filter_region, filter_commodity, filter_status], [filter_json, map_view])
    filter_commodity.change(manual_filter_update, [filter_region, filter_commodity, filter_status], [filter_json, map_view])
    filter_status.change(manual_filter_update, [filter_region, filter_commodity, filter_status], [filter_json, map_view])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
