// Datei: ottoMessageParser.js
class MessageParser {
  constructor(actionProvider) {
    this.actionProvider = actionProvider
  }

  parse(message) {
    if (message.trim()) {
      this.actionProvider.handleUserMessage(message)
    }
  }
}
export default MessageParser
