import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, X, Send, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from '@/components/ui/use-toast';
import axios from 'axios';
import ChatWindow from '@/components/ChatWindow';

// Python API URL
const PYTHON_API_URL = import.meta.env.VITE_CHATBOT_URL || 'http://localhost:5001';

// Initial welcome message
const INITIAL_MESSAGE = {
  id: 1,
  text: "Hi! I'm CashSwap AI Bot. I can help you with:\n\n• Finding people near you for money exchange\n• Answering questions about CashSwap\n• General assistance\n\nHow can I help you today?",
  sender: 'bot',
  users: null
};

const ChatBot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([INITIAL_MESSAGE]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [clarificationState, setClarificationState] = useState(null);
  const [chatUser, setChatUser] = useState(null);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Get user data from localStorage
  const getUserData = () => {
    const userStr = localStorage.getItem('cashswap_user');
    return userStr ? JSON.parse(userStr) : null;
  };

  // Format user list with chat buttons
  const formatUserList = (text, users) => {
    if (!users || users.length === 0) return text;

    // Parse the response text to extract user entries
    const lines = text.split('\n');
    const formattedUsers = [];
    let currentUser = null;
    let userIndex = 0;

    lines.forEach(line => {
      // Check if line starts with a number (e.g., "1. **Name**")
      const nameMatch = line.match(/^\d+\.\s+\*\*(.+?)\*\*/);
      if (nameMatch) {
        if (currentUser) {
          formattedUsers.push(currentUser);
        }
        currentUser = {
          index: userIndex,
          name: nameMatch[1],
          details: [line],
          userData: users[userIndex]
        };
        userIndex++;
      } else if (currentUser && line.trim()) {
        currentUser.details.push(line);
      }
    });

    if (currentUser) {
      formattedUsers.push(currentUser);
    }

    return { formattedUsers, originalText: text };
  };

  // Send message to Python chatbot API
  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
      id: Date.now(),
      text: inputMessage,
      sender: 'user',
      users: null
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = inputMessage;
    setInputMessage('');
    setIsLoading(true);

    try {
      const userData = getUserData();
      const endpoint = clarificationState ? '/clarify' : '/chat';
      
      const payload = {
        message: currentInput,
        user_id: userData?.id || 1,
        user_location: userData?.location ? {
          latitude: userData.location.lat,
          longitude: userData.location.lng,
          radius: 10
        } : {
          latitude: 16.5062,
          longitude: 80.648,
          radius: 10
        },
        ...(clarificationState && {
          clarification_type: clarificationState.type,
          intent_info: clarificationState.intentInfo
        })
      };

      const response = await axios.post(`${PYTHON_API_URL}${endpoint}`, payload);

      // Handle response
      const botMessage = {
        id: Date.now() + 1,
        text: response.data.message,
        sender: 'bot',
        route: response.data.route,
        users: response.data.users || null
      };

      setMessages(prev => [...prev, botMessage]);

      // Update clarification state if needed
      if (response.data.needs_clarification) {
        setClarificationState({
          type: response.data.clarification_type,
          intentInfo: response.data.intent_info
        });
      } else {
        setClarificationState(null);
      }

    } catch (error) {
      console.error('Chatbot error:', error);
      
      let errorText = "Sorry, I encountered an error. Please try again!";
      
      if (error.code === 'ERR_NETWORK') {
        errorText = "⚠️ Cannot connect to AI server. Please make sure Python chatbot is running on port 5001.";
      } else if (error.response?.data?.message) {
        errorText = error.response.data.message;
      }

      const errorMessage = {
        id: Date.now() + 1,
        text: errorText,
        sender: 'bot',
        users: null
      };

      setMessages(prev => [...prev, errorMessage]);
      
      toast({
        title: "Error",
        description: "Failed to get response from chatbot.",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Enter key press
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Handle chat with user
  const handleChatWithUser = (user) => {
    setChatUser({
      id: user.id,
      name: user.name,
      phone: user.phone,
      profilePhoto: user.profile_photo
    });
  };

  // Render message content
  const renderMessageContent = (message) => {
    if (!message.users || message.users.length === 0) {
      return <div className="whitespace-pre-wrap">{message.text}</div>;
    }

    const formatted = formatUserList(message.text, message.users);

    return (
      <div>
        <div className="whitespace-pre-wrap mb-4">
          {formatted.originalText.split('\n').slice(0, 2).join('\n')}
        </div>
        
        <div className="space-y-3 mt-4">
          {formatted.formattedUsers.map((user) => (
            <div
              key={user.index}
              className="bg-white/5 backdrop-blur-sm rounded-lg p-3 border border-white/10 hover:border-purple-400/50 transition-all"
            >
              <div className="whitespace-pre-wrap text-sm mb-2">
                {user.details.join('\n')}
              </div>
              <Button
                onClick={() => handleChatWithUser(user.userData)}
                size="sm"
                className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 mt-2"
              >
                <MessageCircle className="h-3 w-3 mr-2" />
                Chat with {user.name}
              </Button>
            </div>
          ))}
        </div>

        {/* Show footer if present */}
        {formatted.originalText.includes('---') && (
          <div className="mt-4 text-xs text-gray-400 border-t border-white/10 pt-2">
            {formatted.originalText.split('---')[1]}
          </div>
        )}
      </div>
    );
  };

  return (
    <>
      {/* Chat Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="fixed bottom-24 right-4 w-80 md:w-96 h-[600px] glass-effect rounded-2xl shadow-2xl flex flex-col z-50"
          >
            {/* Chat Header */}
            <div className="bg-gradient-to-r from-purple-500 to-pink-500 p-4 rounded-t-2xl flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <MessageCircle className="h-5 w-5 text-white" />
                <span className="font-semibold text-white">CashSwap AI Bot</span>
              </div>
              <Button
                onClick={() => setIsOpen(false)}
                variant="ghost"
                size="icon"
                className="text-white hover:bg-white/20"
              >
                <X className="h-5 w-5" />
              </Button>
            </div>

            {/* Messages Container */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gradient-to-b from-black/10 to-black/20">
              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] p-3 rounded-lg ${
                      message.sender === 'user'
                        ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white'
                        : 'bg-white/10 text-gray-100 backdrop-blur-sm'
                    }`}
                  >
                    {renderMessageContent(message)}
                  </div>
                </motion.div>
              ))}
              
              {isLoading && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex justify-start"
                >
                  <div className="bg-white/10 backdrop-blur-sm rounded-lg p-3 flex items-center space-x-2">
                    <Loader2 className="h-4 w-4 animate-spin text-purple-400" />
                    <span className="text-sm text-gray-300">Thinking...</span>
                  </div>
                </motion.div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 border-t border-white/10 bg-black/20">
              <div className="flex space-x-2">
                <Input
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message..."
                  className="bg-white/10 border-white/20 text-white placeholder:text-gray-400"
                  disabled={isLoading}
                />
                <Button
                  onClick={handleSendMessage}
                  disabled={isLoading || !inputMessage.trim()}
                  className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
                >
                  {isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Floating Chat Button */}
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full shadow-lg flex items-center justify-center z-50 hover:shadow-xl transition-shadow"
      >
        {isOpen ? (
          <X className="h-6 w-6 text-white" />
        ) : (
          <MessageCircle className="h-6 w-6 text-white" />
        )}
      </motion.button>

      {/* Chat Window Modal */}
      {chatUser && (
        <ChatWindow 
          otherUser={chatUser} 
          onClose={() => setChatUser(null)} 
        />
      )}
    </>
  );
};

export default ChatBot;
