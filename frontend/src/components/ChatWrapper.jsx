import React, { useState } from "react";
import ChatBot from "react-chatbotify";
import "react-chatbotify/dist/index.css";
import axios from "axios";

export default function ChatWrapper() {
  const [isLoading, setIsLoading] = useState(false);

  const flow = {
    start: {
      message: "👋 Hi! I'm Aura — your assistant. How can I help today?",
      path: "user_input",
    },
    user_input: {
      user: true,
      message: async (params) => {
        const userMessage = params.userInput;
        if (!userMessage || !userMessage.trim()) return "Please type a message.";

        setIsLoading(true);
        try {
          const res = await axios.post("/api/chat", { message: userMessage });
          const reply = res.data?.reply ?? "Sorry — no reply.";
          return reply;
        } catch (err) {
          console.error(err);
          return "Oops — something went wrong. Try again.";
        } finally {
          setIsLoading(false);
        }
      },
      path: "user_input",
    },
  };

  return (
    <div className="chat-card">
      <div className="chat-header">
        <div className="header-left">
          <img
            src="https://i.ibb.co/6W4kTqZ/bot.png"
            alt="bot-avatar"
            className="header-avatar"
          />
          <div>
            <div className="header-title">Aura — AI Assistant</div>
            <div className="header-sub">Fast replies. Helpful tips.</div>
          </div>
        </div>
      </div>

      <div className="chat-body">
        <ChatBot
          flow={flow}
          settings={{
            header: { title: "" },
            theme: {
              backgroundColor: "#f7f8fc",
              primaryColor: "#7c3aed",
              secondaryColor: "#eef2ff",
              botBubbleColor: "#7c3aed",
              userBubbleColor: "#06b6d4",
              fontColor: "#111827",
            },
            botTyping: isLoading,
            userAvatar: "https://i.ibb.co/9gtb8Cp/user.png",
            botAvatar: "https://i.ibb.co/6W4kTqZ/bot.png",
          }}
        />
      </div>
    </div>
  );
}
