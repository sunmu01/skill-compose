"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { ChatPanel } from "./chat-panel";

interface ChatContextType {
  isOpen: boolean;
  open: (skills?: string[]) => void;
  close: () => void;
  toggle: () => void;
  setDefaultSkills: (skills: string[]) => void;
}

const ChatContext = React.createContext<ChatContextType | null>(null);

export function useChatPanel() {
  const context = React.useContext(ChatContext);
  if (!context) {
    throw new Error("useChatPanel must be used within ChatProvider");
  }
  return context;
}

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = React.useState(false);
  const [defaultSkills, setDefaultSkills] = React.useState<string[]>([]);
  const pathname = usePathname();

  // Hide chat on published pages and fullscreen chat page
  const isPublishedPage = pathname.startsWith('/published/');
  const isFullscreenChatPage = pathname === '/chat';
  const hideChatPanel = isPublishedPage || isFullscreenChatPage;

  const open = React.useCallback((skills?: string[]) => {
    if (skills) {
      setDefaultSkills(skills);
    }
    setIsOpen(true);
  }, []);

  const close = React.useCallback(() => {
    setIsOpen(false);
  }, []);

  const toggle = React.useCallback(() => {
    setIsOpen((prev) => !prev);
  }, []);

  return (
    <ChatContext.Provider
      value={{ isOpen, open, close, toggle, setDefaultSkills }}
    >
      {children}
      {!hideChatPanel && (
        <>
          <ChatPanel
            isOpen={isOpen}
            onClose={close}
            defaultSkills={defaultSkills}
          />
          {/* Floating toggle button */}
          <button
            onClick={toggle}
            className="fixed bottom-6 right-6 w-14 h-14 bg-primary text-primary-foreground rounded-full shadow-lg flex items-center justify-center hover:bg-primary/90 transition-colors z-40"
            title="Toggle Chat Panel"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          </button>
        </>
      )}
    </ChatContext.Provider>
  );
}
