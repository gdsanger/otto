import Chatbot from 'react-chatbot-kit'
import 'react-chatbot-kit/build/main.css'

import config from './ottoConfig'
import MessageParser from './ottoMessageParser'
import ActionProvider from './ottoActionProvider'

export default function ChatOtto() {
  return (
    <div className="p-3 border rounded">
      <Chatbot
        config={config}
        messageParser={MessageParser}
        actionProvider={ActionProvider}
      />
    </div>
  )
}