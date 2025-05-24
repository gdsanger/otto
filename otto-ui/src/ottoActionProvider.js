// Datei: ottoActionProvider.js
class ActionProvider {
  constructor(createChatBotMessage, setStateFunc) {
    this.createChatBotMessage = createChatBotMessage
    this.setState = setStateFunc
  }

  async handleUserMessage(message) {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: [{ role: "user", content: message }] })
    })

    const data = await response.json()
    const botMessage = this.createChatBotMessage(data.reply)
    this.setState((prev) => ({ ...prev, messages: [...prev.messages, botMessage] }))
  }
}
export default ActionProvider