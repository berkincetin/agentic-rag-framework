"""
Gradio UI for the Agentic RAG system.
Supports Turkish characters and multilingual interface.

Turkish Character Support Features:
- UTF-8 encoding configuration for Windows compatibility
- Proper charset headers in all API requests
- Bilingual UI labels (Turkish/English)
- Turkish character preservation in chat messages
- Error messages in both languages
- Proper encoding for API responses

Supported Turkish characters: ğ, Ğ, ı, İ, ö, Ö, ü, Ü, ş, Ş, ç, Ç
"""

import requests
import gradio as gr
import sys
import os

# Set up UTF-8 encoding for Windows compatibility
if sys.platform == "win32":
    import codecs

    # Ensure proper UTF-8 handling for console output
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

# Set environment variable for UTF-8 encoding
os.environ["PYTHONIOENCODING"] = "utf-8"

# API URL
API_URL = "http://localhost:8000"


def ensure_utf8_response(response):
    """Ensure proper UTF-8 encoding for API responses."""
    if response.encoding != "utf-8":
        response.encoding = "utf-8"
    return response


def get_bots():
    """Get the list of available bots from the API."""
    try:
        response = requests.get(
            f"{API_URL}/bots", headers={"Accept": "application/json; charset=utf-8"}
        )
        response = ensure_utf8_response(response)
        if response.status_code == 200:
            data = response.json()
            return data.get("bots", [])
        else:
            return []
    except Exception as e:
        print(f"Error getting bots: {str(e)}")
        return []


def get_bot_info(bot_name):
    """Get information about a specific bot."""
    try:
        response = requests.get(
            f"{API_URL}/bots/{bot_name}",
            headers={"Accept": "application/json; charset=utf-8"},
        )
        response = ensure_utf8_response(response)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Error getting bot info: {str(e)}")
        return None


def format_bot_info(bot_info):
    """Format bot information for display with Turkish support."""
    if not bot_info:
        return "Hiçbir bot seçilmedi. / No bot selected."

    info = f"## {bot_info['name']}\n\n"
    info += f"**Description**: {bot_info['description']}\n\n"

    if bot_info.get("tools"):
        info += "**Tools**:\n"
        for tool in bot_info["tools"]:
            info += f"- {tool}\n"

    if bot_info.get("metadata"):
        info += "\n**Metadata**:\n"
        for key, value in bot_info["metadata"].items():
            if isinstance(value, list):
                info += f"- **{key}**: {', '.join(map(str, value))}\n"
            else:
                info += f"- **{key}**: {value}\n"

    return info


def query_bot(bot_name, message, chat_history):
    """Send a query to the bot and get the response."""
    if not bot_name:
        return "Lütfen önce bir bot seçin. / Please select a bot first.", chat_history

    try:
        payload = {"query": message, "session_id": f"gradio-session-{bot_name}"}

        response = requests.post(
            f"{API_URL}/bots/{bot_name}/query",
            json=payload,
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        response = ensure_utf8_response(response)

        if response.status_code == 200:
            data = response.json()
            bot_response = data.get(
                "response", "Bot'tan yanıt alınamadı. / No response from bot."
            )
            chat_history.append({"role": "user", "content": message})
            chat_history.append({"role": "assistant", "content": bot_response})
            return "", chat_history
        else:
            error_msg = f"Hata / Error: {response.status_code} - {response.text}"
            chat_history.append({"role": "user", "content": message})
            chat_history.append({"role": "assistant", "content": error_msg})
            return "", chat_history
    except Exception as e:
        error_msg = f"Bot sorgulanırken hata oluştu / Error querying bot: {str(e)}"
        chat_history.append({"role": "user", "content": message})
        chat_history.append({"role": "assistant", "content": error_msg})
        return "", chat_history


def on_bot_change(bot_name):
    """Handle bot selection change."""
    if not bot_name:
        return "Hiçbir bot seçilmedi. / No bot selected.", []

    bot_info = get_bot_info(bot_name)
    info_text = format_bot_info(bot_info)

    # When changing bots, we start a new conversation
    # The memory is tied to the session ID, so a new conversation will have a fresh memory

    return info_text, []


def create_ui():
    """Create the Gradio UI."""
    # Get the list of bots
    bots = get_bots()
    bot_names = [bot["name"] for bot in bots]

    # Create the UI with Turkish support
    with gr.Blocks(
        title="Atlas Üniversitesi Chatbotları / Atlas University Chatbots",
        theme=gr.themes.Soft(),
    ) as demo:
        gr.Markdown("# Atlas Üniversitesi Chatbotları / Atlas University Chatbots")
        gr.Markdown(
            "Bir chatbot seçin ve konuşmaya başlayın. Chatbotlar hem Türkçe hem de İngilizce destekler.\n\n"
            "Select a chatbot and start a conversation. The chatbots support both English and Turkish."
        )

        with gr.Row():
            with gr.Column(scale=1):
                bot_dropdown = gr.Dropdown(
                    choices=bot_names,
                    label="Chatbot Seçin / Select a Chatbot",
                    info="Konuşmak istediğiniz chatbotu seçin / Choose which chatbot you want to talk to",
                )
                bot_info = gr.Markdown("Hiçbir bot seçilmedi. / No bot selected.")

            with gr.Column(scale=2):
                chatbot = gr.Chatbot(height=500, type="messages")
                msg = gr.Textbox(
                    show_label=False,
                    placeholder="Mesajınızı buraya yazın... / Type your message here...",
                    container=False,
                )
                clear = gr.Button("Temizle / Clear")

        # Set up event handlers
        bot_dropdown.change(
            on_bot_change, inputs=[bot_dropdown], outputs=[bot_info, chatbot]
        )

        msg.submit(
            query_bot, inputs=[bot_dropdown, msg, chatbot], outputs=[msg, chatbot]
        )

        # Clear chat history and reset memory
        def clear_chat(bot_name):
            if bot_name:
                # Clear memory for the current session
                try:
                    session_id = f"gradio-session-{bot_name}"
                    # Call the clear-memory endpoint
                    response = requests.post(
                        f"{API_URL}/bots/{bot_name}/clear-memory?session_id={session_id}",
                        headers={"Content-Type": "application/json; charset=utf-8"},
                    )
                    response = ensure_utf8_response(response)
                    if response.status_code != 200:
                        print(f"Error clearing memory: {response.text}")
                except Exception as e:
                    print(f"Error clearing memory: {str(e)}")
            return []

        clear.click(clear_chat, inputs=[bot_dropdown], outputs=[chatbot])

        # Initialize with the first bot if available
        if bot_names:
            bot_info_text = format_bot_info(get_bot_info(bot_names[0]))
            bot_info.value = bot_info_text
            bot_dropdown.value = bot_names[0]

    return demo


if __name__ == "__main__":
    # Create and launch the UI
    import argparse

    parser = argparse.ArgumentParser(description="Agentic RAG UI")
    parser.add_argument("--port", type=int, default=7860, help="Port to run the UI on")
    args = parser.parse_args()

    demo = create_ui()
    demo.launch(server_name="0.0.0.0", server_port=args.port)
